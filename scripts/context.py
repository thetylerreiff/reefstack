#!/usr/bin/env python3
"""Supply bounded, local Reefstack context to Codex lifecycle hooks."""

import argparse
import json
import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 65536
EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
ROLES = {"explorer", "mechanical", "worker", "hard_worker", "reviewer", "critical_reviewer"}


def read_json(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("settings exceed the size limit")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("settings must be a JSON object")
    return value


def validate_settings(value):
    if set(value) - {"enabled", "models"}:
        raise ValueError("unsupported settings field")
    if "enabled" in value and not isinstance(value["enabled"], bool):
        raise ValueError("enabled must be boolean")
    models = value.get("models", {})
    if not isinstance(models, dict) or set(models) - ROLES:
        raise ValueError("unsupported model role")
    for spec in models.values():
        if not isinstance(spec, dict) or set(spec) - {"model", "reasoning_effort"}:
            raise ValueError("invalid model settings")
        if "model" in spec and (
            not isinstance(spec["model"], str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,100}", spec["model"])
        ):
            raise ValueError("invalid model name")
        if "reasoning_effort" in spec and (
            not isinstance(spec["reasoning_effort"], str)
            or spec["reasoning_effort"] not in EFFORTS
        ):
            raise ValueError("unsupported reasoning effort")


def load_settings(root=ROOT, data_directory=None):
    settings = read_json(root / "settings.json")
    validate_settings(settings)
    if set(settings.get("models", {})) != ROLES or any(
        set(spec) != {"model", "reasoning_effort"}
        for spec in settings["models"].values()
    ):
        raise ValueError("packaged model settings are incomplete")
    if data_directory:
        override = Path(data_directory) / "settings.json"
        if override.exists():
            values = read_json(override)
            validate_settings(values)
            if "enabled" in values:
                settings["enabled"] = values["enabled"]
            for role, spec in values.get("models", {}).items():
                settings["models"][role].update(spec)
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
            "worker_brief": str(root / "references/worker-brief.md"),
            "review_rubric": str(root / "references/review-rubric.md")
        }
        model_policy = (
            "Configured role defaults (model and effort are separate values; "
            "confirm availability before spawning; preserve the selected parent):\n"
            + json.dumps(settings["models"], sort_keys=True)
        )
    else:
        locations = {
            "worker_brief": str(root / "references/worker-brief.md"),
            "review_rubric": str(root / "references/review-rubric.md")
        }
        model_policy = "The parent's assignment selects your role and model."
    manifest = read_json(root / ".codex-plugin/plugin.json")
    version = manifest.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("plugin version must be a nonempty string")
    context = "\n\n".join([
        "Reefstack " + version + " context loaded.", policy.strip(), model_policy,
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
