#!/usr/bin/env python3
"""Exercise native Codex compaction and restart against an isolated Tally copy.

This supplies per-thread Reefstack guidance; it does not install/trust hooks or
claim native hook delivery. Requires an authenticated local Codex app-server.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
RECORD = ".reefstack/tasks/report-command.md"


class LifecycleError(RuntimeError):
    """Native lifecycle evidence was missing, failed, or unavailable."""


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AppServer:
    """Own one stdio subprocess; never discover or connect to a desktop daemon."""

    def __init__(self, command, cwd, evidence, label, timeout=300):
        self.timeout = timeout
        self.events = []
        self.inbox = queue.Queue()
        self.next_id = 0
        self.disabled_plugins = []
        self.log = (evidence / (label + ".jsonl")).open("w", encoding="utf-8")
        self.stderr = (evidence / (label + ".stderr")).open("w", encoding="utf-8")
        self.process = None
        try:
            self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=self.stderr,
                                            text=True, start_new_session=True)
            self.reader = threading.Thread(target=self._read, daemon=True)
            self.reader.start()
            self.request("initialize", {
                "clientInfo": {"name": "reefstack_lifecycle", "version": "1"},
                "capabilities": {"experimentalApi": True},
            })
            self.send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    self.inbox.put(json.loads(line))
                except ValueError:
                    self.inbox.put(LifecycleError("app-server emitted invalid JSON"))
        finally:
            self.inbox.put(LifecycleError("app-server exited before requested evidence arrived"))

    def send(self, message):
        self.log.write(json.dumps({"direction": "send", "message": message}) + "\n")
        self.log.flush()
        try:
            self.process.stdin.write(json.dumps(message) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise LifecycleError("app-server input closed") from error

    def receive(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LifecycleError("timed out awaiting app-server evidence")
        try:
            message = self.inbox.get(timeout=remaining)
        except queue.Empty as error:
            raise LifecycleError("timed out awaiting app-server evidence") from error
        if isinstance(message, Exception):
            raise message
        if message.get("method", "").startswith(("account/", "chatgptAuthTokens/")):
            message = {key: value for key, value in message.items() if key != "params"}
            message["params"] = {"redacted": "unrelated account/authentication notification"}
        self.log.write(json.dumps({"direction": "receive", "message": message}) + "\n")
        self.log.flush()
        # auto_review handles allowed escalation internally. Never grant requests
        # routed to this headless client, including unexpected user-input requests.
        if "method" in message and "id" in message:
            self.send({"id": message["id"], "error": {
                "code": -32603, "message": "Lifecycle probe cannot approve client requests"}})
            raise LifecycleError("app-server requested client approval/input: " + message["method"])
        self.events.append(message)
        return message

    def request(self, method, params):
        self.next_id += 1
        request_id = self.next_id
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            message = self.receive(deadline)
            if message.get("id") != request_id or "method" in message:
                continue
            if "error" in message:
                raise LifecycleError(method + " failed: " + json.dumps(message["error"]))
            return message.get("result", {})

    def wait_turn(self, thread_id, turn_id=None, start=0, compact=False):
        """Require matching native completion; RPC acknowledgement is insufficient."""
        deadline = time.monotonic() + self.timeout
        cursor = start
        compact_turn = None
        completed_items = {}
        completed_turns = {}
        while True:
            while cursor < len(self.events):
                event = self.events[cursor]
                cursor += 1
                params = event.get("params", {})
                if params.get("threadId") != thread_id:
                    continue
                method = event.get("method")
                if method == "error" and not params.get("willRetry", False):
                    raise LifecycleError("thread error: " + json.dumps(params.get("error")))
                item = params.get("item", {})
                if compact and item.get("type") == "contextCompaction":
                    if method == "item/started":
                        compact_turn = params.get("turnId")
                    elif method == "item/completed":
                        compact_turn = params.get("turnId")
                        completed_items[compact_turn] = item.get("id")
                if method == "turn/completed":
                    turn = params.get("turn", {})
                    completed_turns[turn.get("id")] = turn
                    if compact and turn.get("id") == compact_turn and turn.get("status") != "completed":
                        raise LifecycleError("compaction turn failed: " + json.dumps(turn))
                wanted = compact_turn if compact else turn_id
                turn = completed_turns.get(wanted)
                if turn:
                    if turn.get("status") != "completed":
                        raise LifecycleError("turn did not complete: " + json.dumps(turn))
                    compact_item = completed_items.get(wanted)
                    if not compact or compact_item:
                        return {"thread_id": thread_id, "turn_id": wanted,
                                "status": turn["status"], "compaction_item_id": compact_item}
            self.receive(deadline)

    def turn(self, thread_id, prompt, model, effort):
        start = len(self.events)
        response = self.request("turn/start", {"threadId": thread_id, "model": model,
                                "effort": effort, "disabledPluginIds": self.disabled_plugins,
                                "input": [{"type": "text", "text": prompt}]})
        turn_id = response.get("turn", {}).get("id")
        if not turn_id:
            raise LifecycleError("turn/start did not return a turn ID")
        return self.wait_turn(thread_id, turn_id, start)

    def close(self):
        process = self.process
        if process is not None:
            # The process session was created by us, so no desktop daemon or
            # unrelated process can be part of this group.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            # The leader may exit before a TERM-resistant descendant. Always
            # kill the remainder of our group, even after the leader exited.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout):
                if stream:
                    stream.close()
            if hasattr(self, "reader"):
                self.reader.join(timeout=1)
        self.stderr.close()
        self.log.close()


PARTIAL_PROMPT = """In this Tally project, start the named task report-command: rename the summary
command to report. Create a concise durable task record at {record}. For this
first stage implement the CLI rename and corresponding unit tests only. Do not
update the user README or verification map yet. Run the unit tests, then pause
as requested with a record of the current dirty files, verified work, outstanding
docs/map work, and first next action. Do not commit. Do not delegate this small
staged task. Keep all expense data in a temporary TALLY_HOME.""".format(record=RECORD)

AMENDMENT_PROMPT = """Continue report-command from {record}. Updated requirement: summary must remain
as a backwards-compatible alias of report with identical output and options.
Implement and test that compatibility now. Keep the docs/map work outstanding
for the next stage and update the existing task record to reflect this latest
requirement, what is verified, and what remains. Do not commit or delegate.
Keep expense data in a temporary TALLY_HOME. Pause after this stage.""".format(record=RECORD)

RESUME_PROMPT = """Continue the named report-command task from {record}. Finish the remaining
authorized work and verify the current artifact. The latest requirement still
applies: report is the primary command and summary remains a compatible alias.
Update the user README and existing verification map to describe both commands,
run the relevant checks, and reconcile the whole durable record before your
final handoff. Do not commit or delegate. Use temporary TALLY_HOME data.""".format(record=RECORD)


def check_artifact(project, evidence, label, alias=True):
    """Independent black-box compatibility check plus the fixture's full tests."""
    results = {"cwd": str(project)}
    data = evidence / (label + "-ledger")
    results["TALLY_HOME"] = str(data)
    env = {**os.environ, "TALLY_HOME": str(data)}

    def run(name, argv):
        result = subprocess.run(argv, cwd=project, env=env, text=True, capture_output=True, timeout=60)
        results[name] = {"command": argv, "returncode": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr}
        return result

    for amount, category in [("10", "food"), ("2.25", "food"), ("30", "travel")]:
        run("seed-" + amount, [sys.executable, "-m", "tally", "add", amount, category])
    report = run("report", [sys.executable, "-m", "tally", "report"])
    summary = run("summary", [sys.executable, "-m", "tally", "summary"])
    run("unit", [sys.executable, "-m", "unittest", "-v"])
    results["command_contract"] = (report.returncode == summary.returncode == 0 and report.stdout == summary.stdout
                              if alias else report.returncode == 0 and summary.returncode != 0)
    results["totals_correct"] = all(value in report.stdout for value in ("12.25", "30.00", "42.25"))
    (evidence / (label + "-checks.json")).write_text(json.dumps(results, indent=2) + "\n")
    if not results["command_contract"] or not results["totals_correct"] or any(
            value["returncode"] for key, value in results.items()
            if isinstance(value, dict) and (alias or key != "summary")):
        raise LifecycleError(label + " independent compatibility/unit checks failed")
    return results


def run_lifecycle(output, model, effort, timeout, command):
    output.mkdir(parents=True, exist_ok=False)
    evidence = output / "evidence"
    evidence.mkdir()
    report = {"status": "failed", "started_at": datetime.now(timezone.utc).isoformat(),
              "model": model, "effort": effort, "guidance": "supplied per-thread developerInstructions",
              "native_hook_delivery": "not asserted", "hook_trust_or_installation": "not changed",
              "record_check": "contract keywords/open checkboxes only; semantic review required",
              "host_configuration": "Existing authentication/configuration retained; installed plugins disabled per turn"}
    server = None
    try:
        runner = load_module("lifecycle_fixture", ROOT / "scripts/run_evals.py")
        context = load_module("lifecycle_context", ROOT / "scripts/context.py")
        project, base, _ = runner.prepare_workspace({"fixture": "tally"}, ROOT / "evaluations/fixtures", output)
        guidance = context.context_result("session", {"source": "startup"})["hookSpecificOutput"]["additionalContext"]
        guidance = ("Supplied Reefstack guidance for this isolated thread. This is not proof "
                    "of native hook delivery or installation. Use the source checkout references "
                    "listed below as authoritative, not another installed/cached release.\n\n" + guidance)
        (evidence / "supplied-guidance.txt").write_text(guidance)
        report.update({"project": str(project), "base_commit": base,
                       "guidance_sha256": hashlib.sha256(guidance.encode()).hexdigest()})
        params = {"model": model, "cwd": str(project), "ephemeral": False,
                  "developerInstructions": guidance, "sandbox": "workspace-write",
                  "approvalPolicy": "on-request", "approvalsReviewer": "auto_review"}
        server = AppServer(command, project, evidence, "before-restart", timeout)
        report["first_server_pid"] = server.process.pid
        plugins = server.request("plugin/installed", {"cwds": [str(project)]})
        if "marketplaces" not in plugins:
            raise LifecycleError("cannot enumerate installed plugins for per-thread exclusion")
        disabled_plugins = sorted({plugin["id"] for market in plugins["marketplaces"]
                                   for plugin in market.get("plugins", [])
                                   if plugin.get("installed") and plugin.get("enabled")})
        server.disabled_plugins = disabled_plugins
        report["disabled_plugin_ids"] = disabled_plugins
        response = server.request("thread/start", params)
        thread_id = response.get("thread", {}).get("id")
        if not thread_id:
            raise LifecycleError("thread/start did not return a persistent thread ID")
        report["thread_id"] = thread_id
        report["partial_turn"] = server.turn(thread_id, PARTIAL_PROMPT, model, effort)
        check_artifact(project, evidence, "partial", alias=False)
        record = project / RECORD
        if not record.is_file() or not record.read_text().strip():
            raise LifecycleError("partial stage did not create the durable record")
        # Capture stage evidence before later turns can revise it.
        (evidence / "partial-record.md").write_text(record.read_text())
        (evidence / "partial.diff").write_text(runner.git(project, "diff"))
        if not (evidence / "partial.diff").stat().st_size:
            raise LifecycleError("partial stage produced no tracked implementation changes")
        start = len(server.events)
        server.request("thread/compact/start", {"threadId": thread_id})
        report["compaction"] = server.wait_turn(thread_id, start=start, compact=True)
        report["post_compaction_turn"] = server.turn(thread_id, AMENDMENT_PROMPT, model, effort)
        check_artifact(project, evidence, "post-compaction")
        (evidence / "post-compaction-record.md").write_text(record.read_text())
        server.close()
        server = None
        server = AppServer(command, project, evidence, "after-restart", timeout)
        report["second_server_pid"] = server.process.pid
        server.disabled_plugins = disabled_plugins
        resume = server.request("thread/resume", {key: value for key, value in
                     {**params, "threadId": thread_id}.items() if key != "ephemeral"})
        if resume.get("thread", {}).get("id") != thread_id:
            raise LifecycleError("thread/resume did not restore the same persistent thread")
        report["resume_same_thread"] = True
        report["resumed_turn"] = server.turn(thread_id, RESUME_PROMPT, model, effort)
        check_artifact(project, evidence, "final")
        map_module = runner.MAP_LINT
        map_errors = map_module.lint_directory(project / "docs/verification")
        current_errors = map_module.stale_entries(project / "docs/verification", base)
        docs = (project / "README.md").read_text()
        feature = (project / "docs/verification/category-totals.md").read_text()
        report["map_checks"] = {"lint": map_errors, "current": current_errors,
                                "readme_commands": all(word in docs for word in ("report", "summary")),
                                "feature_commands": all(word in feature for word in ("report", "summary"))}
        if map_errors or current_errors or not all(report["map_checks"][key] for key in ("readme_commands", "feature_commands")):
            raise LifecycleError("final documentation/map checks failed")
        final_record = record.read_text()
        (evidence / "final-record.md").write_text(final_record)
        if "report" not in final_record or "summary" not in final_record or "- [ ]" in final_record:
            raise LifecycleError("final task record omitted current contract or retains open work")
        (evidence / "final.diff").write_text(runner.git(project, "diff"))
        report["status"] = "passed"
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)
    finally:
        if server is not None:
            server.close()
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="fresh evidence/workspace directory")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--timeout", type=float, default=300, help="seconds per request/turn")
    parser.add_argument("--codex", default="codex", help="local Codex executable")
    args = parser.parse_args()
    result = run_lifecycle(args.output.resolve(), args.model, args.effort, args.timeout,
                           [args.codex, "app-server", "--listen", "stdio://"])
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
