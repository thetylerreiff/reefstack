#!/usr/bin/env python3
"""Probe native lifecycle hook transport using an instrumented source snapshot.

Uses invocation-only hook configuration/trust; never installs a plugin, edits
saved trust, overrides HOME/CODEX_HOME, or connects to a desktop app-server.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
import time
import zipfile

from run_lifecycle import AppServer, LifecycleError, load_module

ROOT = Path(__file__).resolve().parent.parent
PROOF_PREFIX = "Native Reefstack delivery proof: "
PROBE_PROMPT = ("Reply with only the token after 'Native Reefstack delivery proof: ' "
                "in your most recent native hook context, or NONE if absent. "
                "Do not use tools or read files. This is a context delivery test.")

# The marker is generated outside model context and read only by the hook.
# The real adapter still receives the actual native hook stdin and emits its
# normal context; instrumentation appends one proof token and records transport.
WRAPPER = '''import json, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parent
payload = sys.stdin.buffer.read(65537)
mode = sys.argv[1]
command = ([sys.executable, str(root / "reefstack/scripts/handoff_guard.py")] if mode == "handoff"
           else [sys.executable, str(root / "reefstack/scripts/context.py"), mode])
result = subprocess.run(command, input=payload, capture_output=True, timeout=10)
if result.returncode:
    sys.stderr.buffer.write(result.stderr)
    raise SystemExit(result.returncode)
output = json.loads(result.stdout)
if mode != "handoff":
    context = output["hookSpecificOutput"]["additionalContext"]
    markers = json.loads((root / "markers.json").read_text())
    token = markers[mode]
    output["hookSpecificOutput"]["additionalContext"] = context + "\\n\\nNative Reefstack delivery proof: " + token
record = {"input": json.loads(payload), "command": command, "output": output}
with (root / "hook-executions.jsonl").open("a") as stream:
    stream.write(json.dumps(record) + "\\n")
print(json.dumps(output))
'''


def toml(value):
    """Small serializer for the strings, booleans, arrays and tables we own."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ",".join(toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(toml(key) + "=" + toml(item) for key, item in value.items()) + "}"
    raise TypeError("unsupported TOML value")


def hook_rows(response):
    if not response.get("data"):
        raise LifecycleError("hooks/list returned no entries")
    rows = []
    for entry in response["data"]:
        if entry.get("errors") or entry.get("warnings"):
            raise LifecycleError("hook discovery errors/warnings: " + json.dumps(entry))
        rows.extend(entry.get("hooks", []))
    return rows


def state_for(rows, trust=False):
    """Disable all ambient hooks and optionally trust only our native config."""
    state = {}
    for row in rows:
        ours = row.get("source") == "sessionFlags"
        if row.get("isManaged") and row.get("enabled"):
            raise LifecycleError("cannot isolate an enabled managed hook")
        state[row["key"]] = {"enabled": ours}
        if ours and trust:
            state[row["key"]]["trusted_hash"] = row["currentHash"]
    if not any(row.get("source") == "sessionFlags" for row in rows):
        raise LifecycleError("native invocation hooks were not discovered")
    return state


def verify_isolation(rows, trusted):
    ours = [row for row in rows if row.get("source") == "sessionFlags"]
    if {row["eventName"] for row in ours} != {"sessionStart", "subagentStart", "stop"}:
        raise LifecycleError("expected native SessionStart, SubagentStart, and Stop hooks")
    for row in rows:
        if row in ours:
            expected = "trusted" if trusted else "untrusted"
            if not row.get("enabled") or row.get("trustStatus") != expected:
                raise LifecycleError("native hook trust state did not match " + expected)
        elif row.get("enabled"):
            raise LifecycleError("ambient hook remains enabled: " + row["key"])


def final_text(events, thread_id, turn_id):
    return "\n".join(event["params"]["item"]["text"] for event in events
                     if event.get("method") == "item/completed"
                     and event.get("params", {}).get("threadId") == thread_id
                     and event["params"].get("turnId") == turn_id
                     and event["params"].get("item", {}).get("type") == "agentMessage"
                     and event["params"]["item"].get("phase") == "final_answer")


def hook_proof(events, thread_id, token, event_name="sessionStart", turn_id=None):
    def identity(params):
        run = params.get("run", {})
        return (params.get("turnId"), run.get("id"), run.get("startedAt"))
    starts = {identity(event.get("params", {})) for event in events
              if event.get("method") == "hook/started"
              and event.get("params", {}).get("threadId") == thread_id}
    for event in events:
        if event.get("method") != "hook/completed":
            continue
        params = event.get("params", {})
        run = params.get("run", {})
        if params.get("threadId") != thread_id or run.get("eventName") != event_name:
            continue
        if turn_id is not None and params.get("turnId") != turn_id:
            continue
        if run.get("source") != "sessionFlags" or run.get("status") != "completed":
            continue
        if identity(params) not in starts or run.get("sourcePath") != "/<session-flags>/config.toml":
            continue
        context = "\n".join(entry.get("text", "") for entry in run.get("entries", [])
                            if entry.get("kind") == "context")
        if PROOF_PREFIX + token in context and "Reefstack " in context:
            return {"thread_id": thread_id, "hook_run_id": run["id"],
                    "hook_turn_id": params.get("turnId"),
                    "event_name": event_name, "source": run["source"],
                    "source_path": run["sourcePath"], "context_sha256": hashlib.sha256(context.encode()).hexdigest()}
    raise LifecycleError("missing matching native hook execution/context proof for " + event_name)


def assert_no_tools(events, thread_id, turn_id, allow_delegation=False):
    allowed = {"userMessage", "agentMessage", "reasoning"}
    for event in events:
        params = event.get("params", {})
        if (event.get("method") not in {"item/started", "item/completed"}
                or params.get("threadId") != thread_id or params.get("turnId") != turn_id):
            continue
        item = params.get("item", {})
        if item.get("type") in allowed:
            continue
        if allow_delegation and (item.get("type") == "subAgentActivity" or
                (item.get("type") == "collabAgentToolCall" and item.get("tool") in {"spawnAgent", "wait"})):
            continue
        raise LifecycleError("model used a tool during the no-tool visibility probe")


def saved_config_fingerprints():
    # Read hashes only; do not copy private configuration into evidence.
    root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            if (root / name).is_file() else None for name in ("config.toml", "hooks.json", "AGENTS.md")}


def handoff_outcomes(records, thread_id, link):
    """Require a real rejection followed by a quiet, corrected Stop payload."""
    blocked = None
    for row in records:
        payload, output = row.get("input", {}), row.get("output", {})
        if payload.get("hook_event_name") != "Stop" or payload.get("session_id") != thread_id:
            continue
        if output.get("decision") == "block" and payload.get("last_assistant_message") == "Done":
            blocked = row
        elif blocked is not None and output == {} and link in payload.get("last_assistant_message", ""):
            return blocked, row
    return None


def stop_runs(events, thread_id, turn_id, status="completed"):
    starts, completed = set(), []
    for event in events:
        params = event.get("params", {})
        run = params.get("run", {})
        if (params.get("threadId") != thread_id or params.get("turnId") != turn_id
                or run.get("eventName") != "stop" or run.get("source") != "sessionFlags"
                or run.get("sourcePath") != "/<session-flags>/config.toml"):
            continue
        identity = (run.get("id"), run.get("startedAt"))
        if event.get("method") == "hook/started":
            starts.add(identity)
        elif event.get("method") == "hook/completed" and run.get("status") == status and identity in starts:
            completed.append(run)
    return completed


def probe_handoff(server, output, project, thread, model, effort):
    helper = load_module("native_task_handoff", output / "reefstack/scripts/task_handoff.py")
    record = project / ".reefstack/tasks/native-handoff.md"
    record.parent.mkdir(parents=True)
    record.write_text("# Native handoff\n\n## Current state\nComplete.\n\n## Resume\nComplete; no remaining action.\n")
    receipt = helper.read_record(record)
    command = shlex.join([sys.executable, str(output / "reefstack/scripts/task_handoff.py"), str(record)])
    prompt = ("This is a bounded native handoff test. Run " + command +
              ". Do not edit files. Intentionally reply with exactly Done, omitting the link on your FIRST answer only. "
              "If the native handoff validator requests a correction, follow that feedback: rerun the helper "
              "and return its exact Record line. Do not do other work.")
    events_start = len(server.events)
    log = output / "hook-executions.jsonl"
    records_start = len(log.read_text().splitlines())
    initial = server.request("turn/start", {"threadId": thread, "model": model, "effort": effort,
                            "disabledPluginIds": server.disabled_plugins,
                            "input": [{"type": "text", "text": prompt}]})["turn"]["id"]
    deadline = time.monotonic() + server.timeout
    outcomes = None
    while outcomes is None:
        records = [json.loads(line) for line in log.read_text().splitlines()[records_start:]]
        outcomes = handoff_outcomes(records, thread, receipt["markdown_link"])
        if outcomes is None:
            server.receive(deadline)
    rejected, corrected = outcomes
    corrected_turn = corrected["input"]["turn_id"]
    completion = server.wait_turn(thread, corrected_turn, start=events_start)
    events = server.events[events_start:]
    if not stop_runs(events, thread, rejected["input"]["turn_id"], "blocked") or not stop_runs(events, thread, corrected_turn):
        raise LifecycleError("handoff correction lacks matching native Stop events")
    # The second helper call must actually have read the unchanged fixture.
    reads = []
    for event in events:
        params, item = event.get("params", {}), event.get("params", {}).get("item", {})
        if (event.get("method") == "item/completed" and params.get("threadId") == thread
                and item.get("type") == "commandExecution" and item.get("exitCode") == 0):
            for line in item.get("aggregatedOutput", "").split("\n"):
                if line.startswith(helper.RECEIPT_PREFIX):
                    reads.append(json.loads(line[len(helper.RECEIPT_PREFIX):]))
    if len(reads) < 2 or reads[-1] != receipt or helper.read_record(record) != receipt:
        raise LifecycleError("handoff correction missing repeated unchanged-record readback")
    return {"initial_turn_id": initial, "corrected_turn_id": completion["turn_id"],
            "native_rejection_observed": True, "final_link_correct": True,
            "record_sha256": receipt["sha256"], "record_unchanged": True,
            "readbacks": len(reads)}


def prepare(output):
    package = load_module("hook_package", ROOT / "scripts/package.py")
    archive = output / "source.zip"
    package.build_archive(archive)
    with zipfile.ZipFile(archive) as stream:
        stream.extractall(output)
    (output / "native_hook_probe.py").write_text(WRAPPER)
    config = json.loads((output / "reefstack/hooks/hooks.json").read_text())["hooks"]
    for name, groups in config.items():
        mode = {"SessionStart": "session", "SubagentStart": "subagent", "Stop": "handoff"}[name]
        for group in groups:
            for handler in group["hooks"]:
                if handler["type"] != "command":
                    raise LifecycleError("unexpected source hook handler")
                handler["command"] = shlex.join([sys.executable, str(output / "native_hook_probe.py"), mode])
    (output / "native-hooks.json").write_text(json.dumps(config, indent=2) + "\n")
    return config, hashlib.sha256(archive.read_bytes()).hexdigest()


def run_hook_delivery(output, model, effort, timeout, codex, subagent=True):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    project = output / "workspace"
    project.mkdir()
    evidence = output / "evidence"
    evidence.mkdir()
    report = {"status": "failed", "started_at": datetime.now(timezone.utc).isoformat(),
              "delivery_route": "native invocation hook configuration with instrumented packaged source",
              "plugin_installation_or_discovery": "not asserted", "saved_hook_trust_or_config": "not changed",
              "home_environment": "inherited without override", "model": model, "effort": effort}
    before_config = saved_config_fingerprints()
    server = None
    try:
        config, report["source_sha256"] = prepare(output)
        command = [codex, "app-server", "--listen", "stdio://", "-c", "hooks=" + toml(config)]
        report["codex_version"] = subprocess.run([codex, "--version"], text=True, capture_output=True,
                                                 check=True, timeout=10).stdout.strip()
        report["app_server_command"] = command
        # Discovery alone starts no thread and executes no lifecycle hooks.
        server = AppServer(command, project, evidence, "discovery", timeout)
        report["native_initialize"] = server.events[0].get("result")
        report["server_processes"] = {"discovery": server.process.pid}
        rows = hook_rows(server.request("hooks/list", {"cwds": [str(project)]}))
        state = state_for(rows)
        report["discovered_hooks"] = rows
        plugins = server.request("plugin/installed", {"cwds": [str(project)]})
        if "marketplaces" not in plugins:
            raise LifecycleError("cannot enumerate plugins for isolation")
        disabled = sorted({plugin["id"] for market in plugins["marketplaces"]
                           for plugin in market.get("plugins", []) if plugin.get("installed") and plugin.get("enabled")})
        server.close()
        server = None
        common = {"cwd": str(project), "model": model, "sandbox": "read-only",
                  "approvalPolicy": "never", "config": {"project_doc_max_bytes": 0}}
        def open_server(label, trusted):
            instance = AppServer(command + ["-c", "hooks.state=" + toml(state_for(rows, trusted))],
                                 project, evidence, label, timeout)
            try:
                checked = hook_rows(instance.request("hooks/list", {"cwds": [str(project)]}))
                verify_isolation(checked, trusted)
                instance.disabled_plugins = disabled
                report["server_processes"][label] = instance.process.pid
                return instance
            except Exception:
                instance.close()
                raise
        def marker(stage):
            token = stage + "_" + secrets.token_hex(16)
            (output / "markers.json").write_text(json.dumps({"session": token, "subagent": token}))
            return token
        marker("untrusted")
        server = open_server("untrusted", False)
        thread = server.request("thread/start", {**common, "ephemeral": True})["thread"]["id"]
        turn = server.turn(thread, PROBE_PROMPT, model, effort)
        assert_no_tools(server.events, thread, turn["turn_id"])
        if final_text(server.events, thread, turn["turn_id"]).strip() != "NONE":
            raise LifecycleError("untrusted hook negative control did not return NONE")
        if (output / "hook-executions.jsonl").exists():
            raise LifecycleError("untrusted native hook unexpectedly executed")
        report["untrusted_negative_control"] = "passed"
        server.close()
        server = None
        token = marker("startup")
        server = open_server("startup-compact", True)
        thread = server.request("thread/start", {**common, "ephemeral": False})["thread"]["id"]
        report["thread_id"] = thread
        def proof_turn(stage, expected, hook_turn=None):
            turn = server.turn(thread, PROBE_PROMPT, model, effort)
            assert_no_tools(server.events, thread, turn["turn_id"])
            if final_text(server.events, thread, turn["turn_id"]).strip() != expected:
                raise LifecycleError(stage + " native hook token was not model-visible")
            proof = hook_proof(server.events, thread, expected, turn_id=hook_turn or turn["turn_id"])
            proof["turn_id"] = turn["turn_id"]
            proof["model_visible"] = True
            records = [json.loads(line) for line in (output / "hook-executions.jsonl").read_text().splitlines()]
            if not any(row["input"].get("source") == stage and
                       PROOF_PREFIX + expected in row["output"]["hookSpecificOutput"]["additionalContext"]
                       for row in records):
                raise LifecycleError("missing actual native stdin source " + stage)
            report[stage] = proof
        proof_turn("startup", token)
        token = marker("compact")
        start = len(server.events)
        server.request("thread/compact/start", {"threadId": thread})
        report["compaction"] = server.wait_turn(thread, start=start, compact=True)
        proof_turn("compact", token)
        report["compact"]["delivery_timing"] = "first turn after native compaction completes"
        server.close()
        server = None
        token = marker("resume")
        server = open_server("resume-subagent", True)
        resumed = server.request("thread/resume", {**common, "threadId": thread})
        if resumed["thread"]["id"] != thread:
            raise LifecycleError("resume changed native thread identity")
        proof_turn("resume", token)
        report["resume"]["scope"] = "same persisted thread in a new owned app-server process"
        if subagent:
            token = marker("subagent")
            start = len(server.events)
            prompt = ("This delivery test explicitly authorizes one child agent. Spawn exactly one child agent "
                      "to reply with only the token after 'Native Reefstack delivery proof: ' in its most recent "
                      "native hook context, or NONE if absent. Do not provide any token in the child prompt. "
                      "The child must not use tools or read files. Wait for its answer and return that answer verbatim. "
                      "Do not do other work.")
            turn = server.turn(thread, prompt, model, effort)
            assert_no_tools(server.events, thread, turn["turn_id"], allow_delegation=True)
            records = [json.loads(line) for line in (output / "hook-executions.jsonl").read_text().splitlines()]
            child_records = [row for row in records if row["input"].get("hook_event_name") == "SubagentStart"
                             and PROOF_PREFIX + token in row["output"]["hookSpecificOutput"]["additionalContext"]]
            if len(child_records) != 1:
                raise LifecycleError("expected one native SubagentStart invocation")
            if final_text(server.events, thread, turn["turn_id"]).strip() != token:
                raise LifecycleError("child native hook token was not returned to parent")
            child = child_records[0]["input"]
            child_id = child.get("agent_id")
            proof = hook_proof(server.events[start:], child_id, token, "subagentStart", child.get("turn_id"))
            child_readback = server.request("thread/read", {"threadId": child_id, "includeTurns": True})
            (evidence / "child-readback.json").write_text(json.dumps(child_readback, indent=2) + "\n")
            child_items = [item for child_turn in child_readback.get("thread", {}).get("turns", [])
                           for item in child_turn.get("items", [])]
            if not child_items or any(item.get("type") not in {"userMessage", "agentMessage", "reasoning"}
                                      for item in child_items):
                raise LifecycleError("child readback missing or contains a tool/file-read path")
            if token not in [item.get("text", "").strip() for item in child_items
                             if item.get("type") == "agentMessage"]:
                raise LifecycleError("child readback does not independently confirm token")
            report["subagent"] = {"model_visible_via_child_reply": True,
                                  "native_stdin": child, "parent_turn_id": turn["turn_id"],
                                  "hook_proof": proof, "child_no_tools": True}
        else:
            report["subagent"] = {"status": "not requested"}
        report["handoff_guard"] = probe_handoff(server, output, project, thread, model, effort)
        report["status"] = "passed"
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)
    finally:
        if server is not None:
            server.close()
        report["saved_config_hashes_before"] = before_config
        report["saved_config_hashes_after"] = saved_config_fingerprints()
        report["saved_config_unchanged"] = before_config == report["saved_config_hashes_after"]
        if not report["saved_config_unchanged"]:
            report["status"] = "failed"
            report["error"] = "Saved configuration changed during the probe; attribution requires inspection"
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--effort", default="low")
    parser.add_argument("--timeout", default=120, type=float)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--skip-subagent", action="store_true")
    args = parser.parse_args()
    result = run_hook_delivery(args.output.resolve(), args.model, args.effort, args.timeout,
                               args.codex, not args.skip_subagent)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
