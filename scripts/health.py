#!/usr/bin/env python3
"""Validate the package and exercise hooks without claiming host activation."""

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent


def inside_file(relative):
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents or not path.is_file():
        raise ValueError("invalid or missing package path: " + relative)
    return path


def check_feature_map():
    spec = importlib.util.spec_from_file_location("reefstack_map_lint", inside_file("scripts/map_lint.py"))
    map_lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(map_lint)
    # Agents copy the template, so it must pass the lint it documents.
    errors = map_lint.lint_files(map_lint.template_files(inside_file("references/feature-map-template.md")))
    if errors:
        raise ValueError("feature map template fails lint: " + "; ".join(errors))
    if not (ROOT / "docs/verification").exists():
        return "not_present"
    errors = map_lint.lint_directory(ROOT / "docs/verification")
    if errors:
        raise ValueError("feature map fails lint: " + "; ".join(errors))
    return "pass"


def check_package():
    # Codex ignores hooks when a root Agent Plugins plugin.json is present.
    if (ROOT / "plugin.json").exists():
        raise ValueError("root plugin.json suppresses Codex plugin hooks; use .codex-plugin/plugin.json")
    manifest = json.loads(inside_file(".codex-plugin/plugin.json").read_text())
    if manifest.get("name") != "reefstack" or not isinstance(manifest.get("version"), str) or not manifest["version"].strip():
        raise ValueError("unexpected plugin identity")
    hooks = json.loads(inside_file(manifest["hooks"]).read_text())["hooks"]
    inside_file(manifest["extensions"]["com.openai"]["onboardingSkill"])
    if set(hooks) != {"SessionStart", "SubagentStart"}:
        raise ValueError("unexpected hook events")
    session_matcher = re.compile(hooks["SessionStart"][0]["matcher"])
    if not all(session_matcher.fullmatch(source) for source in ("startup", "resume", "clear", "compact")):
        raise ValueError("session matcher omits a lifecycle source")
    names = []
    for skill in sorted((ROOT / "skills").iterdir()):
        text = inside_file(str(skill.relative_to(ROOT) / "SKILL.md")).read_text()
        if not text.startswith("---\n") or "\n---\n" not in text:
            raise ValueError("missing frontmatter: " + skill.name)
        header = text.split("\n---\n", 1)[0]
        if f"\nname: {skill.name}\n" not in header + "\n" or "\ndescription: " not in header:
            raise ValueError("invalid skill metadata: " + skill.name)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            local = (skill / target.split("#", 1)[0]).resolve()
            if ROOT not in local.parents or not local.is_file():
                raise ValueError("broken skill reference: " + target)
        names.append(skill.name)
    if set(names) != {"reefstack", "grill", "ground", "design", "deliver", "diagnose", "verify", "review", "setup", "map"}:
        raise ValueError("unexpected skills")
    env = dict(os.environ)
    env.pop("PLUGIN_DATA", None)
    env["PLUGIN_ROOT"] = str(ROOT)
    for mode, event in (("session", "SessionStart"), ("subagent", "SubagentStart")):
        for source in (("startup", "resume", "clear", "compact") if mode == "session" else (None,)):
            payload = {"hook_event_name": event}
            if source:
                payload["source"] = source
            handler = hooks[event][0]["hooks"][0]
            expected_command = 'python3 "${PLUGIN_ROOT}/scripts/context.py" ' + mode
            if handler["command"] != expected_command:
                raise ValueError("unexpected hook command")
            run = subprocess.run(
                handler["command"], shell=True,
                input=json.dumps(payload), text=True, capture_output=True,
                timeout=5, env=env, check=True
            )
            result = json.loads(run.stdout)["hookSpecificOutput"]
            if result["hookEventName"] != event or not result["additionalContext"]:
                raise ValueError("hook did not return context")
    feature_map = check_feature_map()
    return {"package": "pass", "hook_handlers": "pass", "skills": names,
            "feature_map_template": "pass", "feature_map": feature_map,
            "host_installation": "not_checked", "hook_trust": "not_checked",
            "native_context_delivery": "not_checked", "behavioral_evaluation": "not_checked"}


def main():
    try:
        report = check_package()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"package": "fail", "reason": str(error)}))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
