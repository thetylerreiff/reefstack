import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_health", ROOT / "scripts/health.py")
HEALTH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HEALTH)


class WorkflowReferenceTests(unittest.TestCase):
    def test_packaged_workflow_links_resolve(self):
        HEALTH.check_workflow_references()

    def test_missing_resume_procedure_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            shutil.copytree(ROOT / "references", root / "references")
            shutil.copytree(ROOT / "skills", root / "skills")
            shutil.copytree(ROOT / "harness", root / "harness")
            (root / "references/playbooks/resume.md").unlink()
            with mock.patch.object(HEALTH, "ROOT", root), self.assertRaises(ValueError):
                HEALTH.check_workflow_references()

    def test_nested_playbook_links_cannot_be_missing_or_escape_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "plugin"
            shutil.copytree(ROOT / "references", root / "references")
            shutil.copytree(ROOT / "skills", root / "skills")
            shutil.copytree(ROOT / "harness", root / "harness")
            target = root / "references/playbooks/resume.md"
            original = target.read_text()
            outside = Path(directory) / "outside.md"
            outside.write_text("not packaged")
            for link in ("../missing.md", "../../../outside.md"):
                with self.subTest(link=link):
                    target.write_text(original + "\n[Required step](" + link + ")\n")
                    with mock.patch.object(HEALTH, "ROOT", root), self.assertRaisesRegex(
                        ValueError, "broken workflow reference"
                    ):
                        HEALTH.check_workflow_references()

    def test_each_added_playbook_is_required_and_its_dependencies_resolve(self):
        names = ("refactoring", "performance", "prototype", "opening-pr", "pr-follow-up", "shipping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for folder in ("references", "skills", "harness"):
                shutil.copytree(ROOT / folder, root / folder)
            with mock.patch.object(HEALTH, "ROOT", root):
                HEALTH.check_workflow_references()
                for name in names:
                    path = root / "references/playbooks" / (name + ".md")
                    original = path.read_bytes()
                    path.unlink()
                    with self.subTest(name=name), self.assertRaises(ValueError):
                        HEALTH.check_workflow_references()
                    path.write_bytes(original)
                (root / "harness/pr-watch.md").unlink()
                with self.assertRaisesRegex(ValueError, "broken workflow reference"):
                    HEALTH.check_workflow_references()


if __name__ == "__main__":
    unittest.main()
