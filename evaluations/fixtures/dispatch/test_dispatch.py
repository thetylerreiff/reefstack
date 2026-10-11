import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.orders = self.root / "orders.json"
        self.customers = self.root / "customers.json"
        self.output = self.root / "manifest.csv"
        self.orders.write_text(json.dumps([{"id": "P1", "customer_id": "C1", "grams": 501}]))
        self.customers.write_text(json.dumps([{"id": "C1", "name": "Doe, Jo", "zone": "local"}]))

    def tearDown(self):
        self.directory.cleanup()

    def run_manifest(self, *extra):
        return subprocess.run([sys.executable, "-m", "dispatch", "manifest",
                               "--orders", str(self.orders), "--customers", str(self.customers),
                               "--output", str(self.output), *extra],
                              text=True, capture_output=True,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def test_manifest_quotes_customer_and_adds_weight_band(self):
        result = self.run_manifest()
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(list(csv.reader(io.StringIO(self.output.read_text())))[1],
                         ["P1", "Doe, Jo", "local", "standard", "430"])

    def test_express_adds_surcharge(self):
        self.assertEqual(self.run_manifest("--express").returncode, 0)
        self.assertIn(b"express,630\r\n", self.output.read_bytes())

    def test_unknown_customer_preserves_existing_output(self):
        self.output.write_bytes(b"previous manifest\n")
        self.customers.write_text("[]")
        result = self.run_manifest()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "Error: order P1: unknown customer C1\n")
        self.assertEqual(self.output.read_bytes(), b"previous manifest\n")


if __name__ == "__main__":
    unittest.main()
