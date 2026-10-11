import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("handoff_evaluations", ROOT / "scripts/run_evals.py")
EVALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALS)
HANDOFF = EVALS.HANDOFF


def event(kind, **fields):
    return json.dumps({"type": "item.completed", "item": {"type": kind, **fields}})


class TaskHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        self.record = self.project / ".reefstack/tasks/import #1 (final).md"
        self.record.parent.mkdir(parents=True)
        self.record.write_text("# Import\n\n## Resume\nComplete; no remaining action.\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self):
        return subprocess.run([sys.executable, str(ROOT / "scripts/task_handoff.py"), str(self.record)],
                              text=True, capture_output=True)

    def tool_event(self, output=None, status=0):
        return event("command_execution", command="python3 /plugin/scripts/task_handoff.py record.md",
                     aggregated_output=self.invoke().stdout if output is None else output, exit_code=status)

    def message(self, text=None):
        return event("agent_message", text=HANDOFF.read_record(self.record)["markdown_link"] if text is None else text)

    def test_helper_reads_actual_file_without_writing_and_escapes_link(self):
        before = self.record.stat().st_mtime_ns, self.record.read_bytes()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout.split("\n", 1)[0].removeprefix(HANDOFF.RECEIPT_PREFIX))
        self.assertEqual(receipt, HANDOFF.read_record(self.record))
        self.assertEqual(receipt["content"], self.record.read_text())
        self.assertIn("import%20%231%20%28final%29.md", receipt["markdown_link"])
        self.assertEqual(result.stdout.split("\n")[-2], "Record: " + receipt["markdown_link"])
        self.assertEqual(before, (self.record.stat().st_mtime_ns, self.record.read_bytes()))
        self.assertEqual(list(self.record.parent.iterdir()), [self.record])

    def test_real_helper_and_final_link_pass(self):
        transcript = self.tool_event() + "\n" + self.message()
        self.assertEqual(EVALS.check_task_handoff(self.project, transcript), [])

    def test_user_output_constraint_can_opt_out_of_native_guard(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/task_handoff.py"),
                                 "--no-guard", str(self.record)], text=True, capture_output=True, check=True)
        receipt = json.loads(result.stdout.split("\n", 1)[0].removeprefix(HANDOFF.RECEIPT_PREFIX))
        self.assertEqual(receipt, {**HANDOFF.read_record(self.record), "native_guard": False})

    def test_both_observed_misses_and_commentary_only_link_fail(self):
        cases = [self.message(), self.tool_event() + "\n" + self.message("Done."),
                 self.message() + "\n" + self.tool_event() + "\n" + self.message("Done."),
                 self.message() + "\n" + self.tool_event()]
        for transcript in cases:
            with self.subTest(transcript=transcript):
                self.assertTrue(EVALS.check_task_handoff(self.project, transcript))

    def test_mistyped_final_link_fails_despite_successful_readback(self):
        link = HANDOFF.read_record(self.record)["markdown_link"]
        mistyped = link.replace("import%20", "imoprt%20")
        self.assertTrue(EVALS.check_task_handoff(self.project, self.tool_event() + "\n" + self.message(mistyped)))

    def test_readback_before_final_edit_is_stale_even_with_same_link(self):
        old = self.tool_event()
        self.record.write_text(self.record.read_text() + "Newer requirement.\n")
        self.assertTrue(EVALS.check_task_handoff(self.project, old + "\n" + self.message()))
        self.assertEqual(EVALS.check_task_handoff(self.project, old + "\n" + self.tool_event()
                                                + "\n" + self.message()), [])

    def test_failed_calls_plain_text_and_unrelated_file_cannot_pass(self):
        self.assertTrue(EVALS.check_task_handoff(self.project, self.tool_event(status=1) + "\n" + self.message()))
        self.assertTrue(EVALS.check_task_handoff(self.project, self.invoke().stdout + self.message()))
        other = self.project / "README.md"
        other.write_text("Not the task record")
        receipt = HANDOFF.read_record(other)
        transcript = self.tool_event(HANDOFF.RECEIPT_PREFIX + json.dumps(receipt)) + "\n" + self.message(receipt["markdown_link"])
        self.assertTrue(EVALS.check_task_handoff(self.project, transcript))

    def test_malformed_events_fail_closed(self):
        for item in (None, [], {"type": "agent_message", "text": []},
                     {"type": "command_execution", "command": None, "exit_code": 0},
                     {"type": "command_execution", "command": "task_handoff.py", "aggregated_output": {}, "exit_code": 0}):
            transcript = json.dumps({"type": "item.completed", "item": item})
            self.assertTrue(EVALS.check_task_handoff(self.project, transcript))

    def test_empty_missing_large_and_non_utf8_records_fail_without_receipt(self):
        for data in (b"", b"x" * (HANDOFF.MAX_RECORD_BYTES + 1), b"\xff"):
            self.record.write_bytes(data)
            result = self.invoke()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
        self.record.unlink()
        self.assertEqual(self.invoke().returncode, 1)
        self.record.mkdir()
        self.assertEqual(self.invoke().returncode, 1)


if __name__ == "__main__":
    unittest.main()
