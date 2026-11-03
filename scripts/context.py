#!/usr/bin/env python3
"""Supply bounded, local Reefstack context to Codex lifecycle hooks."""

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 65536


def read_json(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("settings exceed the size limit")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("settings must be a JSON object")
    return value


def validate_settings(value):
    if set(value) - {"enabled"}:
        raise ValueError("unsupported settings field")
    if "enabled" in value and not isinstance(value["enabled"], bool):
        raise ValueError("enabled must be boolean")


def load_settings(root=ROOT, data_directory=None):
    settings = read_json(root / "settings.json")
    validate_settings(settings)
    if data_directory:
        override = Path(data_directory) / "settings.json"
        if override.exists():
            values = read_json(override)
            validate_settings(values)
            settings.update(values)
    return settings


def context_result(mode, payload, root=ROOT, data_directory=None):
    if not isinstance(payload, dict):
        raise ValueError("hook input must be an object")
    event = {"session": "SessionStart", "subagent": "SubagentStart"}[mode]
    if payload.get("hook_event_name", event) != event:
        raise ValueError("hook event does not match its handler")
    if mode == "session" and payload.get("source", "startup") not in {
        "startup", "resume", "clear", "compact"
    }:
        raise ValueError("unsupported session source")
    settings = load_settings(root, data_directory)
    if not settings.get("enabled", True):
        return {}
    reference = "activation.md" if mode == "session" else "subagent.md"
    policy = (root / "references" / reference).read_text(encoding="utf-8")
    if mode == "session":
        policy += "\n\n" + (root / "harness/codex.md").read_text(encoding="utf-8")
        locations = {
            "coordinator": str(root / "skills/reefstack/SKILL.md"),
            "grill": str(root / "skills/grill/SKILL.md"),
            "resume": str(root / "references/playbooks/resume.md"),
            "map_lint": str(root / "scripts/map_lint.py"),
            "pr_watch": str(root / "harness/pr-watch.md"),
            "worker_brief": str(root / "references/worker-brief.md"),
            "review_rubric": str(root / "references/review-rubric.md")
        }
    else:
        locations = {
            "worker_brief": str(root / "references/worker-brief.md"),
            "review_rubric": str(root / "references/review-rubric.md")
        }
    manifest = read_json(root / ".codex-plugin/plugin.json")
    version = manifest.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("plugin version must be a nonempty string")
    context = "\n\n".join([
        "Reefstack " + version + " context loaded.", policy.strip(),
        "Authoritative packaged references:\n" + json.dumps(locations, sort_keys=True)
    ])
    return {"hookSpecificOutput": {
        "hookEventName": event,
        "additionalContext": context
    }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("session", "subagent"))
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("hook input exceeds the size limit")
        payload = json.loads(raw) if raw.strip() else {}
        result = context_result(args.mode, payload, data_directory=os.environ.get("PLUGIN_DATA"))
    except (OSError, ValueError, KeyError, UnicodeError) as error:
        if isinstance(error, OSError):
            reason = "a required local file could not be read"
        elif isinstance(error, json.JSONDecodeError):
            reason = "invalid JSON input or settings"
        else:
            reason = str(error)
        result = {"systemMessage": "Reefstack context unavailable: " + reason}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
