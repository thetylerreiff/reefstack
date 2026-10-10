import tempfile
import unittest

from pantry.app import Store, export_csv, render_items


class PantryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = Store(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_seeded_items_render(self):
        page = render_items(self.store.items())
        self.assertIn("<td>Rice</td><td>4</td>", page)

    def test_add_replaces_same_name(self):
        self.store.add("rice", 7)
        names = [item["name"] for item in self.store.items()]
        self.assertEqual(names.count("Rice") + names.count("rice"), 1)

    def test_add_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            self.store.add("  ", 1)

    def test_export_has_header_and_rows(self):
        lines = export_csv(self.store.items()).splitlines()
        self.assertEqual(lines[0], "name,quantity")
        self.assertEqual(len(lines), 4)


if __name__ == "__main__":
    unittest.main()
