"""Held-out CLI acceptance checks for the dispatch playbook scenarios.

DISPATCH_PROJECT can point at a retained trial checkout. These tests belong to
the outer suite and are never copied into the project shown to the agent.
They establish behavior, not agent procedure or a speed-improvement claim.
"""

import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
PROJECT = Path(os.environ.get("DISPATCH_PROJECT", ROOT / "evaluations/fixtures/dispatch")).resolve()


class DispatchBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.orders = self.root / "orders.json"
        self.customers = self.root / "customers.json"
        self.output = self.root / "manifest.csv"
        self.write_inputs([], [{"id": "C", "name": "Zoë, \"Lee\"\nNorth", "zone": "local"}])

    def tearDown(self):
        self.directory.cleanup()

    def write_inputs(self, orders, customers=None):
        self.orders.write_text(json.dumps(orders), encoding="utf-8")
        if customers is not None:
            self.customers.write_text(json.dumps(customers), encoding="utf-8")

    def invoke(self, *extra, output=None):
        before = {path: path.read_bytes() for path in (self.orders, self.customers)}
        result = subprocess.run(
            [sys.executable, "-m", "dispatch", "manifest", "--orders", str(self.orders),
             "--customers", str(self.customers), "--output", str(output or self.output), *extra],
            cwd=PROJECT, capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected, "CLI modified an input file")
        return result

    def assert_success(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_empty_input_emits_exact_header_and_overwrites_old_output(self):
        self.output.write_bytes(b"old file")
        self.assert_success(self.invoke())
        self.assertEqual(self.output.read_bytes(), b"order_id,customer,zone,service,postage_cents\r\n")

    def test_weight_boundaries_order_quoting_duplicates_and_first_customer(self):
        # Non-sorted, repeated IDs and an address-book correction are intentional.
        self.write_inputs([{"id": name, "customer_id": "C", "grams": grams}
                           for name, grams in (("Z", 1), ("A", 500), ("Z", 501), ("B", 20000))],
                          [{"id": "C", "name": "Zoë, \"Lee\"\nNorth", "zone": "local"},
                           {"id": "C", "name": "Later correction", "zone": "national"}])
        self.assert_success(self.invoke())
        expected = 'order_id,customer,zone,service,postage_cents\r\n' + ''.join(
            f'{name},"Zoë, ""Lee""\nNorth",local,standard,{amount}\r\n'
            for name, amount in (("Z", 350), ("A", 350), ("Z", 430), ("B", 3470)))
        self.assertEqual(self.output.read_bytes(), expected.encode("utf-8"))

    def test_each_zone_and_express_preserve_integer_postage(self):
        self.write_inputs([{"id": str(i), "customer_id": str(i), "grams": 501} for i in range(3)],
                          [{"id": str(i), "name": zone, "zone": zone}
                           for i, zone in enumerate(("local", "national", "international"))])
        self.assert_success(self.invoke("--express"))
        rows = list(csv.reader(io.StringIO(self.output.read_text(encoding="utf-8"))))
        self.assertEqual([row[-2:] for row in rows[1:]],
                         [["express", "630"], ["express", "780"], ["express", "1480"]])

    def test_invalid_late_row_has_no_partial_write_or_output_creation(self):
        for grams in (0, -1, 20001, True, 1.5, "500", None):
            for existing in (False, True):
                with self.subTest(grams=grams, existing=existing):
                    self.write_inputs([{"id": "valid", "customer_id": "C", "grams": 500},
                                       {"id": "bad", "customer_id": "C", "grams": grams}])
                    if existing:
                        self.output.write_bytes(b"previous\r\nmanifest\n")
                    elif self.output.exists():
                        self.output.unlink()
                    result = self.invoke()
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (2, b"", b"Error: order bad: grams must be an integer from 1 to 20000\n"))
                    if existing:
                        self.assertEqual(self.output.read_bytes(), b"previous\r\nmanifest\n")
                    else:
                        self.assertFalse(self.output.exists())

    def test_invalid_data_errors_preserve_output(self):
        scenarios = [
            ([{"id": "P", "customer_id": "missing", "grams": 1}], [],
             "order P: unknown customer missing"),
            ([{"id": "P", "customer_id": "C", "grams": 1}],
             [{"id": "C", "name": "Lee", "zone": "moon"}], "order P: unknown zone moon"),
            ([{"id": "P", "grams": 1}], [], "'customer_id'"),
            ({}, [], "orders and customers must be lists"),
            ([], {}, "orders and customers must be lists"),
        ]
        for orders, customers, error in scenarios:
            with self.subTest(error=error):
                self.write_inputs(orders, customers)
                self.output.write_bytes(b"original")
                result = self.invoke()
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, b"", ("Error: " + error + "\n").encode()))
                self.assertEqual(self.output.read_bytes(), b"original")

    def test_unused_customer_rows_do_not_change_lazy_error_order(self):
        # Indexing the whole address book eagerly is tempting but can surface
        # an error in rows the original command never needed to inspect.
        self.write_inputs([], [{}])
        self.assert_success(self.invoke())
        self.write_inputs([{"id": "P", "customer_id": "C", "grams": 500}],
                          [{"id": "C", "name": "Lee", "zone": "local"}, {}])
        self.assert_success(self.invoke())
        self.assertEqual(self.output.read_bytes(),
                         b"order_id,customer,zone,service,postage_cents\r\n"
                         b"P,Lee,local,standard,350\r\n")
        self.write_inputs([{"id": "P", "customer_id": "C", "grams": 0}], [{}])
        result = self.invoke()
        self.assertEqual((result.returncode, result.stderr),
                         (2, b"Error: order P: grams must be an integer from 1 to 20000\n"))

        # Reading the missing order key early must not hide an earlier
        # malformed address-book row. Preserve both neighboring cases too.
        for customers, error in (([{}], "'id'"), ([], "'customer_id'"),
                                 ([{"id": "C"}], "'customer_id'")):
            with self.subTest(customers=customers):
                self.write_inputs([{"id": "P", "grams": 500}], customers)
                self.output.write_bytes(b"previous manifest")
                result = self.invoke()
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (2, b"", ("Error: " + error + "\n").encode()))
                self.assertEqual(self.output.read_bytes(), b"previous manifest")

    def test_bad_json_and_missing_output_directory_are_errors_without_side_effects(self):
        self.orders.write_bytes(b"[")
        self.output.write_bytes(b"original")
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(b"Error: "))
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"original")
        self.write_inputs([])
        destination = self.root / "absent" / "manifest.csv"
        result = self.invoke(output=destination)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(b"Error: "))
        self.assertFalse(destination.parent.exists())

    def test_generated_workload_is_repeatable_and_full_csv_matches_independent_oracle(self):
        # Exercise the whole CLI over meaningful joins; timings are intentionally
        # absent from unit assertions because host load is not a correctness oracle.
        command = [sys.executable, str(PROJECT / "make_workload.py"), str(self.root),
                   "--orders", "1200", "--customers", "103"]
        subprocess.run(command, cwd=PROJECT, check=True, capture_output=True)
        first = (self.orders.read_bytes(), self.customers.read_bytes())
        subprocess.run(command, cwd=PROJECT, check=True, capture_output=True)
        self.assertEqual(first, (self.orders.read_bytes(), self.customers.read_bytes()))
        self.assert_success(self.invoke())
        first_csv = self.output.read_bytes()
        self.assert_success(self.invoke())
        self.assertEqual(first_csv, self.output.read_bytes())
        rows = list(csv.reader(io.StringIO(first_csv.decode("utf-8"))))
        self.assertEqual(len(rows), 1201)
        orders = json.loads(first[0])
        customers = {entry["id"]: entry for entry in json.loads(first[1])}
        for row, order in zip(rows[1:], orders):
            customer = customers[order["customer_id"]]
            base = (350, 500, 1200)[("local", "national", "international").index(customer["zone"])]
            started_bands = (order["grams"] + 499) // 500
            self.assertEqual(row, [order["id"], customer["name"], customer["zone"], "standard",
                                   str(base + 80 * (started_bands - 1))])


if __name__ == "__main__":
    unittest.main()
