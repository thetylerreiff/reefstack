import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_package", ROOT / "scripts/package.py")
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


class PackageTests(unittest.TestCase):
    def make_source(self, parent):
        root = Path(parent) / "source"
        for directory in ("assets", "evaluations", "hooks", "references", "scripts",
                          "skills/example", "harness", "settings", ".github/workflows",
                          ".agents", "tests", "__pycache__", "build"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        for relative, contents in (
            ("plugin.json", "{}"),
            ("README.md", "readme"),
            ("LICENSE", "license"),
            ("VERIFICATION.md", "verification"),
            ("settings.json", "{}"),
            ("evaluations/cases.json", "[]"),
            ("CONTRIBUTING.md", "contributor notes"),
            ("assets/icon.png", "icon"),
            ("hooks/hooks.json", "hooks"),
            ("references/guide.md", "guide"),
            ("scripts/package.py", "builder"),
            ("skills/example/SKILL.md", "skill"),
            ("harness/codex.md", "harness"),
            ("settings/settings.json", "settings"),
            (".github/workflows/checks.yml", "workflow"),
            (".agents/private.md", "private"),
            ("tests/test.py", "tests"),
            ("__pycache__/secret.pyc", "cache"),
            ("build/output", "build output"),
            (".env", "secret"),
            ("unrelated/data.txt", "unrelated"),
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        return root

    def test_archive_layout_includes_plugin_content_and_excludes_repository_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            archive_path = Path(directory) / "plugin.zip"
            PACKAGE.build_archive(archive_path, source=source)
            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
                self.assertTrue(names)
                self.assertEqual({name.split("/", 1)[0] for name in names}, {"reefstack"})
                self.assertIn("reefstack/plugin.json", names)
                self.assertIn("reefstack/README.md", names)
                self.assertIn("reefstack/LICENSE", names)
                self.assertIn("reefstack/VERIFICATION.md", names)
                self.assertIn("reefstack/CONTRIBUTING.md", names)
                self.assertIn("reefstack/settings.json", names)
                self.assertIn("reefstack/evaluations/cases.json", names)
                for included in (
                    "assets/icon.png", "hooks/hooks.json", "references/guide.md",
                    "scripts/package.py", "skills/example/SKILL.md", "harness/codex.md",
                    "settings/settings.json", "tests/test.py",
                ):
                    self.assertIn("reefstack/" + included, names)
                for excluded in (
                    ".github/workflows/checks.yml", ".agents/private.md",
                    "__pycache__/secret.pyc", "build/output", ".env", "unrelated/data.txt",
                ):
                    self.assertNotIn("reefstack/" + excluded, names)

    def test_repeated_builds_are_byte_for_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            PACKAGE.build_archive(first, source=source)
            PACKAGE.build_archive(second, source=source)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            output = Path(directory) / "plugin.zip"
            output.write_bytes(b"keep me")
            with self.assertRaisesRegex(PACKAGE.PackageError, "overwrite"):
                PACKAGE.build_archive(output, source=source)
            self.assertEqual(output.read_bytes(), b"keep me")

    def test_output_must_be_outside_source_and_parent_must_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            with self.assertRaisesRegex(PACKAGE.PackageError, "outside"):
                PACKAGE.build_archive(source / "inside.zip", source=source)
            with self.assertRaisesRegex(PACKAGE.PackageError, "does not exist"):
                PACKAGE.build_archive(Path(directory) / "missing" / "plugin.zip", source=source)

    def test_internal_file_symlink_is_packaged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            (source / "assets/alias.txt").symlink_to("icon.png")
            archive_path = Path(directory) / "plugin.zip"
            PACKAGE.build_archive(archive_path, source=source)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(archive.read("reefstack/assets/alias.txt"), b"icon")

    def test_symlink_escaping_source_is_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(directory)
            outside = Path(directory) / "outside.txt"
            outside.write_text("outside")
            (source / "assets/escape.txt").symlink_to(outside)
            output = Path(directory) / "plugin.zip"
            with self.assertRaisesRegex(PACKAGE.PackageError, "escapes source"):
                PACKAGE.build_archive(output, source=source)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
