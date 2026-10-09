import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_context", ROOT / "scripts/context.py")
CONTEXT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTEXT)


class ContextTests(unittest.TestCase):
    def test_all_session_sources_supply_packaged_context(self):
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source):
                output = CONTEXT.context_result("session", {"source": source})["hookSpecificOutput"]
                self.assertEqual(output["hookEventName"], "SessionStart")
                self.assertIn(str(ROOT / "skills/reefstack/SKILL.md"), output["additionalContext"])

    def test_partial_override_preserves_other_roles_and_effort(self):
        with tempfile.TemporaryDirectory() as data:
            Path(data, "settings.json").write_text(json.dumps({"models": {"worker": {"model": "gpt-6.1-sol"}}}))
            defaults = CONTEXT.load_settings()
            expected = copy.deepcopy(defaults)
            expected["models"]["worker"]["model"] = "gpt-6.1-sol"
            self.assertEqual(CONTEXT.load_settings(data_directory=data), expected)
            self.assertEqual(CONTEXT.load_settings(), defaults)

    def test_disabled_setting_supplies_no_context(self):
        with tempfile.TemporaryDirectory() as data:
            Path(data, "settings.json").write_text('{"enabled": false}')
            self.assertEqual(CONTEXT.context_result("session", {}, data_directory=data), {})
            self.assertEqual(CONTEXT.context_result("subagent", {}, data_directory=data), {})

    def test_subagent_receives_role_context_without_coordinator(self):
        result = CONTEXT.context_result("subagent", {})["hookSpecificOutput"]
        self.assertEqual(result["hookEventName"], "SubagentStart")
        self.assertNotIn(str(ROOT / "skills/reefstack/SKILL.md"), result["additionalContext"])
        self.assertNotIn(str(ROOT / "skills/grill/SKILL.md"), result["additionalContext"])
        self.assertIn(str(ROOT / "references/review-rubric.md"), result["additionalContext"])

    def test_grill_is_available_to_root_across_session_sources(self):
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source):
                text = CONTEXT.context_result("session", {"source": source})["hookSpecificOutput"]["additionalContext"]
                self.assertIn(str(ROOT / "skills/grill/SKILL.md"), text)
                self.assertTrue((ROOT / "skills/grill/SKILL.md").is_file())

    def test_context_uses_version_from_relocated_manifest(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "relocated"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", ".git", "dist"))
            manifest = json.loads((root / ".codex-plugin/plugin.json").read_text())
            manifest["version"] = "3.2.1"
            (root / ".codex-plugin/plugin.json").write_text(json.dumps(manifest))
            for mode in ("session", "subagent"):
                text = CONTEXT.context_result(mode, {}, root=root)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("Reefstack 3.2.1 context loaded.", text)

    def test_codex_manifest_declares_hooks_without_a_root_manifest(self):
        # Codex 0.162 loads no plugin hooks when a root Agent Plugins plugin.json exists.
        self.assertFalse((ROOT / "plugin.json").exists())
        manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(manifest["hooks"], "./hooks/hooks.json")
        self.assertTrue((ROOT / manifest["extensions"]["com.openai"]["onboardingSkill"]).is_file())

    def test_untrusted_input_is_not_relayed(self):
        sentinel = "UNTRUSTED_PAYLOAD_SHOULD_NEVER_APPEAR"
        output = CONTEXT.context_result("subagent", {"agent_type": sentinel, "prompt": sentinel})
        self.assertNotIn(sentinel, json.dumps(output))

    def test_relocated_package_with_spaces_resolves_local_paths(self):
        with tempfile.TemporaryDirectory() as parent:
            relocated = Path(parent) / "A plugin with spaces"
            shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns("__pycache__", ".git", "dist"))
            result = CONTEXT.context_result("session", {}, root=relocated)
            text = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn(str(relocated / "skills/reefstack/SKILL.md"), text)
            self.assertNotIn(str(ROOT / "skills/reefstack/SKILL.md"), text)

    def test_declared_shell_hook_runs_from_a_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as parent:
            relocated = Path(parent) / "A plugin with spaces"
            shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns("__pycache__", ".git", "dist"))
            hooks = json.loads((relocated / "hooks/hooks.json").read_text())["hooks"]
            env = dict(os.environ)
            env.pop("PLUGIN_DATA", None)
            env["PLUGIN_ROOT"] = str(relocated)
            for event in ("SessionStart", "SubagentStart"):
                run = subprocess.run(hooks[event][0]["hooks"][0]["command"],
                                     shell=True, input=json.dumps({"hook_event_name": event}),
                                     text=True, capture_output=True, env=env, check=True)
                context = json.loads(run.stdout)["hookSpecificOutput"]
                self.assertEqual(context["hookEventName"], event)
                self.assertIn(str(relocated / "references/worker-brief.md"), context["additionalContext"])

    def test_invalid_model_and_effort_overrides_are_rejected(self):
        for value in ({"models": {"worker": {"model": "bad\ntext"}}},
                      {"models": {"reviewer": {"reasoning_effort": "unknown"}}},
                      {"enabled": "false"}, {"unsupported": True},
                      {"models": {"unknown-role": {}}}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CONTEXT.validate_settings(value)

    def test_mismatched_event_and_unknown_source_are_rejected(self):
        for payload in ({"hook_event_name": "Stop"}, {"source": "unknown"}, []):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                CONTEXT.context_result("session", payload)

    def test_cli_reports_bad_input_without_false_activation(self):
        env = dict(os.environ)
        env.pop("PLUGIN_DATA", None)
        for raw in ("not-json", "[]", "x" * (CONTEXT.MAX_BYTES + 1)):
            with self.subTest(length=len(raw)):
                run = subprocess.run([sys.executable, str(ROOT / "scripts/context.py"), "session"],
                                     input=raw, text=True, capture_output=True, env=env, check=True)
                output = json.loads(run.stdout)
                self.assertIn("systemMessage", output)
                self.assertNotIn("hookSpecificOutput", output)

    def test_session_context_includes_delegation_roles_and_harness_notes(self):
        text = CONTEXT.context_result("session", {})["hookSpecificOutput"]["additionalContext"]
        for role in CONTEXT.ROLES:
            self.assertIn(f'"{role}"', text)
        self.assertIn("Codex delegation mechanics", text)
        self.assertNotIn("Codex delegation mechanics",
                         CONTEXT.context_result("subagent", {})["hookSpecificOutput"]["additionalContext"])

    def test_context_fits_configured_limits(self):
        # additionalContextLimit is in approximate tokens; 3 characters per token is conservative.
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
        for mode, event in (("session", "SessionStart"), ("subagent", "SubagentStart")):
            with self.subTest(mode=mode):
                limit = hooks[event][0]["hooks"][0]["additionalContextLimit"]
                text = CONTEXT.context_result(mode, {})["hookSpecificOutput"]["additionalContext"]
                self.assertLess(len(text) / 3, limit)

    def test_core_procedures_stay_harness_neutral(self):
        for path in [*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob("references/*.md")]:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(), r"(?i)codex|gpt-|\b(sol|luna|astra)\b|PLUGIN_DATA")

    def test_missing_reference_returns_warning(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent)
            shutil.copy(ROOT / "settings.json", root / "settings.json")
            with self.assertRaises(OSError):
                CONTEXT.context_result("session", {}, root=root)


if __name__ == "__main__":
    unittest.main()
