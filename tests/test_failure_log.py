from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("Seen", "Cause", "Became", "Enforced by")
OUTCOMES = {"skill change", "check", "map fix", "none yet"}


def entries(text):
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        title, *lines = block.strip().splitlines()
        fields = {}
        for line in lines:
            match = re.fullmatch(r"- ([^:]+): (.+)", line)
            if line.strip():
                fields[match.group(1) if match else "malformed: " + line] = match.group(2) if match else ""
        yield title, fields


class FailureLogTests(unittest.TestCase):
    def test_malformed_lines_are_reported_not_raised(self):
        fields = dict(entries("### X\n\n- Seen: today\nstray text\n"))["X"]
        self.assertIn("malformed: stray text", fields)

    def test_entries_name_an_outcome_and_an_existing_enforcer(self):
        found = list(entries((ROOT / "docs/failure-log.md").read_text()))
        self.assertTrue(found)
        for title, fields in found:
            with self.subTest(entry=title):
                self.assertEqual(tuple(fields), FIELDS)
                self.assertIn(fields["Became"], OUTCOMES)
                if fields["Became"] == "check":
                    paths = re.findall(r"`((?:scripts|tests|skills|references)/[^` ]+)", fields["Enforced by"])
                    self.assertTrue(paths, "a check must name the file that enforces it")
                    for path in paths:
                        self.assertTrue((ROOT / path).is_file(), path)
                    # A named test must still exist in the file it is named with.
                    for path, test in re.findall(r"`(tests/[^`]+\.py)` (test_\w+)", fields["Enforced by"]):
                        self.assertIn(f"def {test}(", (ROOT / path).read_text(), test)

    def test_enforcement_reference_documents_the_same_entry_shape(self):
        text = (ROOT / "references/enforcement.md").read_text()
        for field in FIELDS:
            self.assertIn(f"- {field}:", text)
        for outcome in OUTCOMES:
            self.assertIn(outcome, text)


if __name__ == "__main__":
    unittest.main()
