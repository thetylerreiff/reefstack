import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("handoff_guard", ROOT / "scripts/handoff_guard.py")
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class HandoffGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="reefstack guard ")
        self.project = Path(self.temp.name).resolve()
        self.record = self.project / ".reefstack/tasks/import #1 (final).md"
        self.record.parent.mkdir(parents=True)
        self.record.write_text("# Import\n\n## Resume\nComplete; no remaining action.\n")
        self.transcript = self.project / "transcript.jsonl"
        self.payload = {
            "session_id": "native-thread-123", "turn_id": "native-turn-456",
            "transcript_path": str(self.transcript), "cwd": str(self.project),
            "hook_event_name": "Stop", "stop_hook_active": False,
            "last_assistant_message": "Done.",
        }

    def tearDown(self):
        self.temp.cleanup()

    def helper(self, record=None):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/task_handoff.py"), str(record or self.record)],
            capture_output=True, text=True, check=True,
        )
        return result.stdout

    def event(self, output=None, command=None, **item_fields):
        # Matches the captured native event_msg shape, including command argv
        # inside a code-mode execution (not the outer custom_tool_call source).
        if command is None:
            command = ["/bin/zsh", "-lc", "python3 " + shlex.quote(
                str(ROOT / "scripts/task_handoff.py")) + " " + shlex.quote(str(self.record))]
        item = {
            "type": "CommandExecution", "id": "exec-native-id", "process_id": "123",
            "command": command, "cwd": self.project.as_uri(), "parsed_cmd": [],
            "source": "unified_exec_startup", "status": "completed",
            "stdout": self.helper() if output is None else output, "stderr": "",
            "exit_code": 0, "duration": {"secs": 0, "nanos": 9250},
        }
        item["aggregated_output"] = item["stdout"]
        item.update(item_fields)
        return {
            "timestamp": "2026-10-11T03:39:18.042Z", "ordinal": 12,
            "type": "event_msg", "payload": {
                "type": "item_completed", "thread_id": self.payload["session_id"],
                "turn_id": self.payload["turn_id"], "item": item,
                "started_at_ms": 1791689958042, "completed_at_ms": 1791689958042,
            },
        }

    def write_events(self, *events):
        self.transcript.write_text("".join(json.dumps(event) + "\n" for event in events))

    def invoke(self, payload=None, raw=None, env=None):
        environment = os.environ.copy()
        environment.pop("PLUGIN_DATA", None)
        environment.update(env or {})
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/handoff_guard.py")],
            input=raw if raw is not None else json.dumps(payload or self.payload),
            capture_output=True, text=True, env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(result.stdout.splitlines()), 1)
        return json.loads(result.stdout)

    def link(self):
        return GUARD.task_handoff.read_record(self.record)["markdown_link"]

    def assert_blocked(self, result):
        self.assertEqual(result.get("decision"), "block", result)
        self.assertIn("Re-run python3", result["reason"])
        self.assertIn("do not edit product files", result["reason"])

    def test_real_helper_native_event_and_exact_final_link_pass_without_writes(self):
        self.write_events(self.event())
        self.payload["last_assistant_message"] = "Done.\n\nRecord: " + self.link()
        before = {str(p): (p.stat().st_mtime_ns, p.read_bytes())
                  for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(self.invoke(), {})
        after = {str(p): (p.stat().st_mtime_ns, p.read_bytes())
                 for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_missing_and_mistyped_link_request_exact_record_line(self):
        self.write_events(self.event())
        for final in ("Done.", self.link().replace("import", "imoprt"), None, [self.link()]):
            with self.subTest(final=final):
                self.payload["last_assistant_message"] = final
                result = self.invoke()
                self.assert_blocked(result)
                self.assertIn("\nRecord: " + self.link(), result["reason"])

    def test_unicode_record_separators_preserve_receipt(self):
        self.record.write_text("# Record\nText with \u2028 and \u2029 separators.\n")
        self.write_events(self.event())
        self.payload["last_assistant_message"] = self.link()
        self.assertEqual(self.invoke(), {})

    def test_heredoc_example_is_not_a_helper_invocation(self):
        for operator, end in (("<<'EXAMPLE'", "EXAMPLE"), ("<<-EXAMPLE", "\tEXAMPLE")):
            command = "cat " + operator + "\npython3 task_handoff.py .reefstack/tasks/example.md\n" + end
            self.write_events(self.event(output="example text", command=["/bin/zsh", "-lc", command]))
            self.assertEqual(self.invoke(), {})

    def test_stale_readback_fails_then_new_readback_passes(self):
        old = self.event()
        self.record.write_text(self.record.read_text() + "New requirement.\n")
        self.write_events(old)
        self.payload["last_assistant_message"] = self.link()
        self.assert_blocked(self.invoke())
        self.write_events(old, self.event())
        self.assertEqual(self.invoke(), {})

    def test_last_failed_or_invalid_helper_overrides_prior_success(self):
        good = self.event()
        self.payload["last_assistant_message"] = self.link()
        cases = [
            {"exit_code": 1}, {"status": "failed"}, {"exit_code": True},
            {"aggregated_output": ""}, {"aggregated_output": "REEFSTACK_HANDOFF broken"},
            {"aggregated_output": self.helper() * 2}, {"aggregated_output": {}},
        ]
        for fields in cases:
            with self.subTest(fields=fields):
                self.write_events(good, self.event(**fields))
                self.assert_blocked(self.invoke())

    def test_receipt_requires_complete_exact_shape(self):
        receipt = GUARD.task_handoff.read_record(self.record)
        variants = [dict(receipt, extra="not the receipt"), dict(receipt, content="wrong"),
                    dict(receipt, sha256="wrong"), dict(receipt, markdown_link="wrong"),
                    {key: value for key, value in receipt.items() if key != "content"}]
        for variant in variants:
            with self.subTest(variant=variant):
                self.write_events(self.event(output="REEFSTACK_HANDOFF " + json.dumps(variant)))
                self.assert_blocked(self.invoke())

    def test_stdout_fallback_and_direct_argv_are_supported(self):
        event = self.event(command=[sys.executable, str(ROOT / "scripts/task_handoff.py"), str(self.record)])
        del event["payload"]["item"]["aggregated_output"]
        self.write_events(event)
        self.payload["last_assistant_message"] = self.link()
        self.assertEqual(self.invoke(), {})

    def test_no_guard_honors_explicit_command_without_claiming_validation(self):
        receipt = dict(GUARD.task_handoff.read_record(self.record), native_guard=False)
        event = self.event(
            output="REEFSTACK_HANDOFF " + json.dumps(receipt),
            command=["python3", str(ROOT / "scripts/task_handoff.py"), "--no-guard", str(self.record)],
        )
        self.write_events(event)
        self.assertEqual(self.invoke(), {})
        self.record.write_text(self.record.read_text() + "Changed.\n")
        self.assertEqual(self.invoke(), {})
        self.record.unlink()
        event["payload"]["item"]["exit_code"] = 1
        self.write_events(event)
        self.assertEqual(self.invoke(), {})
        event["payload"]["item"]["command"][-1] = str(self.project / "outside.md")
        self.write_events(event)
        self.assertEqual(self.invoke(), {})

    def test_successful_receipt_opt_out_survives_later_changes(self):
        receipt = dict(GUARD.task_handoff.read_record(self.record), native_guard=False)
        self.write_events(self.event(output="REEFSTACK_HANDOFF " + json.dumps(receipt)))
        self.record.write_text("Changed since the explicit opt-out.")
        self.assertEqual(self.invoke(), {})
        self.record.unlink()
        self.assertEqual(self.invoke(), {})

    def test_existing_alternate_record_and_explicit_opt_out_stay_uncovered(self):
        alternate = self.project / "TASK.md"
        alternate.write_text("Existing canonical record.\n")
        for flags in ([], ["--no-guard"]):
            command = [sys.executable, str(ROOT / "scripts/task_handoff.py"), *flags, str(alternate)]
            output = subprocess.run(command, text=True, capture_output=True, check=True).stdout
            self.write_events(self.event(output=output, command=command))
            with patch.object(GUARD.task_handoff, "read_record", side_effect=AssertionError("outside read")):
                self.assertEqual(GUARD.guard_result(self.payload), {})

    def test_no_guard_cannot_hide_a_failed_helper_attempt(self):
        receipt = dict(GUARD.task_handoff.read_record(self.record), native_guard=False)
        self.write_events(self.event(output="REEFSTACK_HANDOFF " + json.dumps(receipt), exit_code=1))
        self.assert_blocked(self.invoke())

    def test_record_write_heredoc_then_helper_in_one_native_command(self):
        command = "cat > " + shlex.quote(str(self.record)) + " <<'RECORD'\n"
        command += "# Record\nThis record's text has an unmatched quote.\nRECORD\n"
        command += "python3 " + shlex.quote(str(ROOT / "scripts/task_handoff.py")) + " "
        command += shlex.quote(str(self.record))
        self.write_events(self.event(command=["/bin/zsh", "-lc", command]))
        self.assert_blocked(self.invoke())

    def test_wrong_thread_turn_and_non_native_events_are_ignored(self):
        thread, turn = self.event(), self.event()
        thread["payload"]["thread_id"] = "other-thread"
        turn["payload"]["turn_id"] = "earlier-turn"
        legacy = {"type": "item.completed", "item": self.event()["payload"]["item"]}
        self.write_events(thread, turn, legacy)
        self.assertEqual(self.invoke(), {})

    def test_small_turn_missing_transcript_and_unsupported_events_stay_quiet(self):
        self.assertEqual(self.invoke(), {})
        self.write_events(self.event(command=["echo", "task_handoff.py"]))
        self.assertEqual(self.invoke(), {})
        self.transcript.write_text("not JSON\nnull\n[]\n{}\n")
        self.assertEqual(self.invoke(), {})
        for fields in ({"transcript_path": None}, {"session_id": None}, {"turn_id": ""}):
            self.assertEqual(self.invoke(dict(self.payload, **fields)), {})

    def test_one_correction_limit_reports_link_without_another_continuation(self):
        self.write_events(self.event())
        self.assert_blocked(self.invoke())
        self.payload["stop_hook_active"] = True
        result = self.invoke()
        self.assertNotIn("decision", result)
        self.assertIn("Record: " + self.link(), result["systemMessage"])
        self.payload["last_assistant_message"] = self.link()
        self.assertEqual(self.invoke(), {})

    def test_disabled_setting_does_not_inspect_transcript(self):
        data = self.project / "plugin data"
        data.mkdir()
        (data / "settings.json").write_text('{"enabled":false}')
        self.write_events(self.event())
        self.assertEqual(self.invoke(env={"PLUGIN_DATA": str(data)}), {})

    def test_malformed_and_oversized_input_return_bounded_diagnostic(self):
        for raw in ("{", "[]", "null", "x" * (GUARD.MAX_INPUT_BYTES + 1)):
            with self.subTest(raw=raw[:20]):
                result = self.invoke(raw=raw)
                self.assertNotIn("decision", result)
                self.assertIn("unavailable", result["systemMessage"])
                self.assertLess(len(result["systemMessage"]), 300)

    def test_outside_and_alternate_paths_are_not_read(self):
        outside = self.project.parent / "secret.md"
        paths = [outside, self.project / "README.md", self.record.parent]
        for path in paths:
            with self.subTest(path=path):
                self.write_events(self.event(command=["python3", "task_handoff.py", str(path)]))
                with patch.object(GUARD.task_handoff, "read_record", side_effect=AssertionError("outside read")):
                    result = GUARD.guard_result(self.payload)
                self.assertEqual(result, {})

    def test_symlink_escape_is_not_read(self):
        link = self.record.parent / "external.md"
        link.symlink_to(self.project / "README.md")
        self.write_events(self.event(command=["python3", "task_handoff.py", str(link)]))
        with patch.object(GUARD.task_handoff, "read_record", side_effect=AssertionError("symlink read")):
            self.assertEqual(GUARD.guard_result(self.payload), {})

    def test_receipt_for_a_different_record_does_not_pass(self):
        other = self.record.parent / "other.md"
        other.write_text("Other record")
        self.write_events(self.event(output=self.helper(other)))
        self.payload["last_assistant_message"] = GUARD.task_handoff.read_record(other)["markdown_link"]
        self.assert_blocked(self.invoke())

    def test_missing_large_and_non_utf8_records_fail_safely(self):
        event = self.event()
        for data in (b"", b"x" * (GUARD.task_handoff.MAX_RECORD_BYTES + 1), b"\xff"):
            self.record.write_bytes(data)
            self.write_events(event)
            self.assert_blocked(self.invoke())
        self.record.unlink()
        self.assert_blocked(self.invoke())

    def test_bounded_tail_discards_partial_first_line_and_retains_current_event(self):
        event = self.event()
        self.transcript.write_bytes(b"x" * (GUARD.MAX_TRANSCRIPT_BYTES + 5) + b"\n"
                                    + (json.dumps(event) + "\n").encode())
        self.payload["last_assistant_message"] = self.link()
        self.assertEqual(self.invoke(), {})

    def test_partial_last_event_and_malformed_lines_cannot_replace_last_helper(self):
        self.write_events(self.event())
        with self.transcript.open("a") as stream:
            stream.write("{bad json}\n" + json.dumps(self.event(exit_code=1))[:-4])
        self.payload["last_assistant_message"] = self.link()
        self.assertEqual(self.invoke(), {})

    def test_complete_last_json_event_without_newline_is_checked(self):
        self.write_events(self.event())
        with self.transcript.open("a") as stream:
            stream.write(json.dumps(self.event(exit_code=1)))
        self.payload["last_assistant_message"] = self.link()
        self.assert_blocked(self.invoke())


if __name__ == "__main__":
    unittest.main()
