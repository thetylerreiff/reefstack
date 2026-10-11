"""Native hook evidence checks and real command transport, without model calls."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("hook_delivery", ROOT / "scripts/run_hook_delivery.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def row(key="ours", source="sessionFlags", event="sessionStart", **extra):
    return {"key": key, "source": source, "eventName": event, "currentHash": "sha256:current",
            "enabled": True, "isManaged": False, "trustStatus": "untrusted", **extra}


class HookDeliveryTests(unittest.TestCase):
    def test_handoff_evidence_requires_rejection_then_correct_link_in_same_thread(self):
        def row(message, output, thread="thread"):
            return {"input": {"hook_event_name": "Stop", "session_id": thread,
                              "last_assistant_message": message}, "output": output}
        rejected = row("Done", {"decision": "block"})
        accepted = row("Record: correct-link", {})
        self.assertEqual(probe.handoff_outcomes([rejected, accepted], "thread", "correct-link"),
                         (rejected, accepted))
        for rows in ([accepted], [accepted, rejected], [rejected, row("wrong-link", {})],
                     [rejected, row("correct-link", {}, "other")],
                     [rejected, row("correct-link", {"systemMessage": "unverified"})]):
            self.assertIsNone(probe.handoff_outcomes(rows, "thread", "correct-link"))

    def test_stop_proof_requires_matching_native_start_and_turn(self):
        run = {"id": "guard", "startedAt": 1, "eventName": "stop", "source": "sessionFlags",
               "sourcePath": "/<session-flags>/config.toml", "status": "completed"}
        events = [{"method": method, "params": {"threadId": "thread", "turnId": "turn", "run": run}}
                  for method in ("hook/started", "hook/completed")]
        self.assertEqual(probe.stop_runs(events, "thread", "turn"), [run])
        self.assertEqual(probe.stop_runs(events[1:], "thread", "turn"), [])
        self.assertEqual(probe.stop_runs(events, "thread", "other"), [])
        self.assertEqual(probe.stop_runs(events, "thread", "turn", "blocked"), [])
        run["status"] = "blocked"
        self.assertEqual(probe.stop_runs(events, "thread", "turn", "blocked"), [run])
        self.assertEqual(probe.stop_runs(events, "thread", "turn"), [])

    @unittest.skipIf(os.name == "nt", "POSIX directory permissions")
    def test_evidence_directory_is_private_even_with_permissive_umask(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "private-evidence"
            previous_umask = os.umask(0o022)
            try:
                with mock.patch.object(probe, "saved_config_fingerprints", return_value={}), \
                     mock.patch.object(probe, "prepare", side_effect=probe.LifecycleError("stop before model call")):
                    result = probe.run_hook_delivery(output, "model", "low", 1, "unused")
            finally:
                os.umask(previous_umask)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            self.assertEqual(result["status"], "failed")
            self.assertTrue((output / "result.json").is_file())

    def test_exact_hash_trust_is_limited_to_invocation_hooks(self):
        rows = [row(), row("ambient", "plugin", trustStatus="trusted")]
        self.assertEqual(probe.state_for(rows, True), {
            "ours": {"enabled": True, "trusted_hash": "sha256:current"},
            "ambient": {"enabled": False}})
        self.assertNotIn("trusted_hash", probe.state_for(rows)["ours"])

    def test_active_managed_hooks_and_discovery_errors_fail_closed(self):
        with self.assertRaises(probe.LifecycleError):
            probe.state_for([row(isManaged=True)])
        for response in ({}, {"data": [{"errors": ["error"], "hooks": []}]},
                         {"data": [{"warnings": ["warning"], "hooks": []}]}):
            with self.subTest(response=response), self.assertRaises(probe.LifecycleError):
                probe.hook_rows(response)

    def test_untrusted_or_ambient_enabled_cannot_pass_isolation(self):
        rows = [row(trustStatus="trusted"), row("child", event="subagentStart", trustStatus="trusted"),
                row("guard", event="stop", trustStatus="trusted")]
        probe.verify_isolation(rows, True)
        with self.assertRaises(probe.LifecycleError):
            probe.verify_isolation(rows, False)
        with self.assertRaises(probe.LifecycleError):
            probe.verify_isolation(rows + [row("ambient", "plugin")], True)

    def test_completed_hook_requires_matched_start_thread_source_and_context(self):
        run = {"id": "run", "status": "completed", "source": "sessionFlags",
               "sourcePath": "/<session-flags>/config.toml", "eventName": "sessionStart",
               "entries": [{"kind": "context", "text": "Reefstack 0.2.7\n" + probe.PROOF_PREFIX + "secret"}]}
        events = [{"method": "hook/started", "params": {"threadId": "thread", "run": run}},
                  {"method": "hook/completed", "params": {"threadId": "thread", "run": run}}]
        self.assertEqual(probe.hook_proof(events, "thread", "secret")["hook_run_id"], "run")
        for changed in (events[1:], [{**events[0], "params": {"threadId": "other", "run": run}}, events[1:][0]]):
            with self.assertRaises(probe.LifecycleError):
                probe.hook_proof(changed, "thread", "secret")
        for field, value in (("status", "failed"), ("source", "plugin"), ("eventName", "subagentStart")):
            modified = json.loads(json.dumps(events))
            modified[1]["params"]["run"][field] = value
            with self.subTest(field=field), self.assertRaises(probe.LifecycleError):
                probe.hook_proof(modified, "thread", "secret")
        with self.assertRaises(probe.LifecycleError):
            probe.hook_proof(events, "thread", "different-secret")
        different_turn = json.loads(json.dumps(events))
        different_turn[0]["params"]["turnId"] = "old-turn"
        different_turn[1]["params"]["turnId"] = "new-turn"
        with self.assertRaises(probe.LifecycleError):
            probe.hook_proof(different_turn, "thread", "secret", turn_id="new-turn")
        with self.assertRaises(probe.LifecycleError):
            probe.hook_proof(events, "thread", "secret", turn_id="other-turn")

    def test_model_evidence_matches_exact_thread_and_turn(self):
        def event(thread, turn, text):
            return {"method": "item/completed", "params": {"threadId": thread, "turnId": turn,
                    "item": {"type": "agentMessage", "phase": "final_answer", "text": text}}}
        events = [event("other", "turn", "wrong"), event("thread", "old", "wrong"),
                  event("thread", "turn", "right")]
        self.assertEqual(probe.final_text(events, "thread", "turn"), "right")

    def test_visibility_probe_rejects_tool_or_file_read_path(self):
        events = [{"method": "item/started", "params": {"threadId": "thread", "turnId": "turn",
                   "item": {"type": "commandExecution"}}}]
        probe.assert_no_tools(events, "other", "turn")
        with self.assertRaises(probe.LifecycleError):
            probe.assert_no_tools(events, "thread", "turn")
        with self.assertRaises(probe.LifecycleError):
            probe.assert_no_tools(events, "thread", "turn", allow_delegation=True)
        events[0]["method"] = "item/completed"
        with self.assertRaises(probe.LifecycleError):
            probe.assert_no_tools(events, "thread", "turn", allow_delegation=True)
        events[0]["params"]["item"] = {"type": "collabAgentToolCall", "tool": "wait"}
        probe.assert_no_tools(events, "thread", "turn", allow_delegation=True)

    def test_wrapper_transports_actual_stdin_to_packaged_adapter(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            probe.prepare(path)
            (path / "markers.json").write_text(json.dumps({"session": "private-token", "subagent": "child-token"}))
            for mode, payload, token in (("session", {"hook_event_name": "SessionStart", "source": "resume"}, "private-token"),
                                          ("subagent", {"hook_event_name": "SubagentStart", "agent_type": "worker"}, "child-token")):
                result = subprocess.run([sys.executable, str(path / "native_hook_probe.py"), mode],
                                        input=json.dumps(payload), text=True, capture_output=True, check=True)
                value = json.loads(result.stdout)
                self.assertIn(probe.PROOF_PREFIX + token, value["hookSpecificOutput"]["additionalContext"])
                self.assertEqual(value["hookSpecificOutput"]["hookEventName"], payload["hook_event_name"])
            records = [json.loads(line) for line in (path / "hook-executions.jsonl").read_text().splitlines()]
            self.assertEqual(records[0]["input"]["source"], "resume")
            self.assertEqual(records[1]["input"]["agent_type"], "worker")
            self.assertTrue(records[0]["command"][1].endswith("reefstack/scripts/context.py"))


if __name__ == "__main__":
    unittest.main()
