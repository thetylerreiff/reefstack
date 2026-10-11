"""Transport regressions do not require credentials or live model calls."""
import importlib.util
import io
import json
from pathlib import Path
import queue
import shutil
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("lifecycle", ROOT / "scripts/run_lifecycle.py")
lifecycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lifecycle)


def event(method, thread="wanted", turn="turn", status="completed", item=None):
    params = {"threadId": thread, "turnId": turn}
    if method == "turn/completed":
        params["turn"] = {"id": turn, "status": status}
    if item:
        params["item"] = {"id": item, "type": "contextCompaction"}
    return {"method": method, "params": params}


def buffered(events):
    server = lifecycle.AppServer.__new__(lifecycle.AppServer)
    server.events = events
    server.timeout = 0.01

    def timeout(deadline):
        raise lifecycle.LifecycleError("timed out awaiting app-server evidence")
    server.receive = timeout
    return server


class LifecycleProtocolTests(unittest.TestCase):
    def test_rejected_compact_or_resume_rpc_fails_closed(self):
        for method in ("thread/compact/start", "thread/resume"):
            server = buffered([])
            server.next_id = 0
            server.send = lambda message: None
            server.receive = lambda deadline: {"id": 1, "error": {"code": -32603, "message": "unavailable"}}
            with self.subTest(method=method), self.assertRaisesRegex(lifecycle.LifecycleError, "unavailable"):
                server.request(method, {"threadId": "thread"})

    def test_turn_matches_both_thread_and_turn(self):
        server = buffered([event("turn/completed", thread="other"),
                           event("turn/completed", turn="old", status="failed"),
                           event("turn/completed")])
        self.assertEqual(server.wait_turn("wanted", "turn")["status"], "completed")

    def test_compaction_requires_completed_item_and_completed_matching_turn(self):
        server = buffered([event("item/started", item="compact"),
                           event("turn/completed", turn="other"),
                           event("item/completed", item="compact"), event("turn/completed")])
        result = server.wait_turn("wanted", compact=True)
        self.assertEqual(result["compaction_item_id"], "compact")
        self.assertEqual(result["turn_id"], "turn")

    def test_compaction_item_cannot_satisfy_a_different_turn(self):
        server = buffered([event("item/completed", turn="old", item="old-item"),
                           event("item/started", turn="new", item="new-item"),
                           event("turn/completed", turn="new")])
        with self.assertRaisesRegex(lifecycle.LifecycleError, "timed out"):
            server.wait_turn("wanted", compact=True)

    def test_rpc_ack_or_started_item_is_not_compaction_success(self):
        for events in ([{"id": 1, "result": {}}],
                       [event("item/started", item="compact"), event("turn/completed")],
                       [event("item/completed", item="compact")],
                       [event("item/completed", thread="other", item="compact"), event("turn/completed")]):
            with self.subTest(events=events), self.assertRaisesRegex(lifecycle.LifecycleError, "timed out"):
                buffered(events).wait_turn("wanted", compact=True)

    def test_old_events_cannot_satisfy_a_new_request(self):
        with self.assertRaisesRegex(lifecycle.LifecycleError, "timed out"):
            buffered([event("turn/completed")]).wait_turn("wanted", "turn", start=1)

    def test_failed_and_interrupted_turns_fail_closed(self):
        for status in ("failed", "interrupted", "inProgress"):
            with self.subTest(status=status), self.assertRaises(lifecycle.LifecycleError):
                buffered([event("turn/completed", status=status)]).wait_turn("wanted", "turn")
        with self.assertRaisesRegex(lifecycle.LifecycleError, "compaction turn failed"):
            buffered([event("item/started", item="compact"),
                      event("turn/completed", status="failed")]).wait_turn("wanted", compact=True)

    def test_nonretryable_thread_error_fails_closed(self):
        with self.assertRaisesRegex(lifecycle.LifecycleError, "thread error"):
            buffered([{"method": "error", "params": {"threadId": "wanted", "error": "denied"}}]).wait_turn("wanted", "turn")

    def test_timeout_eof_and_client_approval_fail_closed(self):
        server = lifecycle.AppServer.__new__(lifecycle.AppServer)
        server.inbox = queue.Queue()
        server.events = []
        server.log = io.StringIO()
        server.send = lambda message: self.assertIn("error", message)
        with self.assertRaisesRegex(lifecycle.LifecycleError, "timed out"):
            server.receive(time.monotonic() + 0.001)
        server.inbox.put(lifecycle.LifecycleError("app-server exited"))
        with self.assertRaisesRegex(lifecycle.LifecycleError, "exited"):
            server.receive(time.monotonic() + 1)
        server.inbox.put({"id": 9, "method": "item/commandExecution/requestApproval"})
        with self.assertRaisesRegex(lifecycle.LifecycleError, "approval/input"):
            server.receive(time.monotonic() + 1)

    def test_account_notifications_are_redacted_from_evidence(self):
        server = lifecycle.AppServer.__new__(lifecycle.AppServer)
        server.inbox = queue.Queue()
        server.events = []
        server.log = io.StringIO()
        server.inbox.put({"method": "account/rateLimits/updated", "params": {"private": "account-state"}})
        result = server.receive(time.monotonic() + 1)
        self.assertNotIn("account-state", server.log.getvalue())
        self.assertIn("redacted", result["params"])

    def test_each_turn_explicitly_preserves_plugin_exclusion(self):
        server = buffered([])
        server.disabled_plugins = ["reefstack@reefstack", "other@example"]
        calls = []
        server.request = lambda method, params: calls.append((method, params)) or {"turn": {"id": "turn"}}
        server.wait_turn = lambda *args: {"status": "completed"}
        server.turn("thread", "continue", "model", "high")
        self.assertEqual(calls[0][1]["disabledPluginIds"], server.disabled_plugins)

    def test_initial_stage_accepts_expected_absence_of_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "tally"
            shutil.copytree(ROOT / "evaluations/fixtures/tally", project)
            for name in ("tally/cli.py", "test_tally.py"):
                path = project / name
                path.write_text(path.read_text().replace('"summary"', '"report"'))
            results = lifecycle.check_artifact(project, root, "partial", alias=False)
            self.assertTrue(results["command_contract"])
            self.assertNotEqual(results["summary"]["returncode"], 0)

    def test_close_kills_term_resistant_descendant_after_leader_exits(self):
        child = "import pathlib, signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); p=pathlib.Path('heartbeat'); exec('while True: p.write_text(str(time.monotonic())); time.sleep(0.02)')"
        script = """import json, pathlib, subprocess, sys, time
subprocess.Popen([sys.executable, '-u', '-c', CHILD])
while not pathlib.Path('heartbeat').exists(): time.sleep(0.01)
for line in sys.stdin:
    message = json.loads(line)
    if 'id' in message:
        print(json.dumps({'id': message['id'], 'result': {}}), flush=True)
""".replace("CHILD", repr(child))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            server = lifecycle.AppServer([sys.executable, "-u", "-c", script], root, root, "resistant", timeout=3)
            server.close()
            time.sleep(0.05)
            last = (root / "heartbeat").read_text()
            time.sleep(0.1)
            self.assertEqual((root / "heartbeat").read_text(), last)
            self.assertIsNotNone(server.process.poll())

    def test_real_subprocess_restart_and_resume_without_daemon(self):
        script = '''import json, pathlib, sys
for line in sys.stdin:
    m = json.loads(line)
    if "id" not in m: continue
    method = m["method"]
    result = {}
    if method == "thread/start":
        pathlib.Path("thread.json").write_text("persisted-thread")
        result = {"thread": {"id": "persisted-thread"}}
    if method == "thread/resume":
        result = {"thread": {"id": pathlib.Path("thread.json").read_text()}}
    print(json.dumps({"id": m["id"], "result": result}), flush=True)
'''
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            command = [sys.executable, "-u", "-c", script]
            first = lifecycle.AppServer(command, root, root, "first", timeout=2)
            try:
                thread = first.request("thread/start", {})["thread"]["id"]
                first_pid = first.process.pid
            finally:
                first.close()
            self.assertIsNotNone(first.process.poll())
            second = lifecycle.AppServer(command, root, root, "second", timeout=2)
            try:
                self.assertNotEqual(second.process.pid, first_pid)
                self.assertEqual(second.request("thread/resume", {"threadId": thread})["thread"]["id"], thread)
            finally:
                second.close()
            self.assertIsNotNone(second.process.poll())
            self.assertTrue((root / "first.jsonl").stat().st_size)
            self.assertTrue((root / "second.jsonl").stat().st_size)


if __name__ == "__main__":
    unittest.main()
