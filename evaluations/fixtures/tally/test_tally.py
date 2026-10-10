import contextlib
import io
import os
import tempfile
import unittest

from tally.cli import main


class TallyTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        os.environ["TALLY_HOME"] = self.home.name

    def tearDown(self):
        self.home.cleanup()
        del os.environ["TALLY_HOME"]

    def run_cli(self, *argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(list(argv))
        return output.getvalue()

    def test_add_then_list(self):
        self.assertEqual(self.run_cli("add", "12.50", "Food", "--note", "lunch"), "Added 12.50 to food\n")
        self.assertIn("12.50  food  lunch", self.run_cli("list"))

    def test_summary_totals_per_category(self):
        self.run_cli("add", "10", "food")
        self.run_cli("add", "2.25", "food")
        self.run_cli("add", "30", "travel")
        lines = self.run_cli("summary").splitlines()
        self.assertEqual(lines[0].split(), ["food", "12.25"])
        self.assertEqual(lines[-1].split(), ["total", "42.25"])

    def test_empty_ledger(self):
        self.assertEqual(self.run_cli("summary"), "No expenses yet\n")


if __name__ == "__main__":
    unittest.main()
