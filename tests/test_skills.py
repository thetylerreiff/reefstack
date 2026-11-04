import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_health_skills", ROOT / "scripts/health.py")
HEALTH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HEALTH)
COORDINATOR = ROOT / "skills/reefstack"


def copy_package(directory):
    root = Path(directory).resolve()
    for name in (".codex-plugin", "skills", "scripts", "evaluations"):
        shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__", "results"))
    return root


class SkillPackageTests(unittest.TestCase):
    def test_coordinator_stays_within_its_budget(self):
        # The coordinator is read on every engineering task: new standing text must replace old text.
        self.assertLessEqual(len((COORDINATOR / "SKILL.md").read_text()) / 4, 2000)

    def test_core_procedures_stay_harness_neutral(self):
        # Host mechanics live only in skills/reefstack/harness/.
        paths = [*ROOT.glob("skills/*/SKILL.md"), *(COORDINATOR / "references").rglob("*.md")]
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(), r"(?i)codex|gpt-|\b(sol|luna|astra)\b|PLUGIN_DATA")

    def test_health_refuses_hooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = copy_package(directory)
            with mock.patch.object(HEALTH, "ROOT", root):
                HEALTH.check_package()
                manifest = root / ".codex-plugin/plugin.json"
                original = manifest.read_text()
                manifest.write_text(json.dumps({**json.loads(original), "hooks": "./hooks/hooks.json"}))
                with self.assertRaisesRegex(ValueError, "skills only"):
                    HEALTH.check_package()
                manifest.write_text(original)
                (root / "hooks").mkdir()
                with self.assertRaisesRegex(ValueError, "skills only"):
                    HEALTH.check_package()

    def test_health_refuses_a_description_the_host_would_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = copy_package(directory)
            skill = root / "skills/grill/SKILL.md"
            text = skill.read_text()
            start = text.index("description: ") + len("description: ")
            end = text.index("\n", start)
            with mock.patch.object(HEALTH, "ROOT", root):
                skill.write_text(text[:start] + "x" * HEALTH.DESCRIPTION_LIMIT + text[end:])
                HEALTH.check_skills()
                skill.write_text(text[:start] + "x" * (HEALTH.DESCRIPTION_LIMIT + 1) + text[end:])
                with self.assertRaisesRegex(ValueError, "exceeds 1024"):
                    HEALTH.check_skills()
                skill.write_text(text[:start] + "Use when: the user asks" + text[end:])
                with self.assertRaisesRegex(ValueError, "plain YAML scalar"):
                    HEALTH.check_skills()
                skill.write_text(text[:start] + text[end:])
                with self.assertRaisesRegex(ValueError, "invalid skill metadata"):
                    HEALTH.check_skills()

    def test_pr_watch_prompt_matches_the_app_format_and_names_the_skill(self):
        template = (COORDINATOR / "harness/pr-watch.md").read_text()
        # The Codex app recognizes a watch by this marker and the URL line beneath it.
        self.assertIn("## Pull request fix automation:\nRepository: <owner/repo>\nPull request: #<number>\n"
                      "Pull request URL: <url>\n", template)
        self.assertIn("This is a heartbeat turn. Continue automatically fixing this pull request.", template)
        # Skills do not carry into heartbeat turns, so the prompt itself must name the coordinator.
        self.assertIn("Use the <$reefstack or $reefstack:reefstack> skill for this turn.", template)


if __name__ == "__main__":
    unittest.main()
