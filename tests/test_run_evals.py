import copy
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_run_evals", ROOT / "scripts/run_evals.py")
RUN_EVALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_EVALS)
CASES = {case["id"]: case for case in RUN_EVALS.load_cases()}
NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
SECRET = "sk-test-SECRET-never-written"

# Stands in for a coding agent: reads the prompt on stdin and edits the project in its working directory.
FAKE_AGENT = textwrap.dedent('''
    import os, pathlib, socket, sys
    prompt = sys.stdin.read()
    print("prompt:", prompt)
    print("visible settings:", sorted(k for k in os.environ if k.startswith("REEFSTACK_") or k == "ANTHROPIC_API_KEY"))
    app = pathlib.Path("pantry/app.py")
    if "Quantitiy" in prompt:
        app.write_text(app.read_text().replace("Quantitiy", "Quantity"))
    if "/export/items.csv" in prompt:
        app.write_text(app.read_text().replace('"/items/export"', '"/export/items.csv"'))
        if os.environ.get("FAKE_UPDATE_MAP"):
            entry = pathlib.Path("docs/verification/items-export.md")
            entry.write_text(entry.read_text().replace("/items/export", "/export/items.csv"))
    try:
        socket.socket().bind(("127.0.0.1", 0))
        print("bind ok")
    except OSError as error:
        print("bind failed:", error)
''')


def verdict(case, passed=True):
    return json.dumps({"criteria": [{"criterion": item, "passed": passed, "reason": "seen in transcript"}
                                    for item in case["rubric"]], "summary": "checked"})


class MockJudge:
    def __init__(self, replies):
        self.replies, self.prompts = list(replies), []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class RunEvalsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.temp = Path(self.directory.name)
        agent_script = self.temp / "agent.py"
        agent_script.write_text(FAKE_AGENT)
        self.agent = {"command": f'"{sys.executable}" "{agent_script}" --model {{model}}',
                      "model": "gpt-6-luna", "timeout": 60}
        self.judge_info = {"provider": "anthropic", "model": "claude-judge"}

    def tearDown(self):
        self.directory.cleanup()

    def suite(self, cases, replies, runs=1, env=None):
        judge = MockJudge(replies)
        with mock.patch.dict(os.environ, {"REEFSTACK_JUDGE_MODEL": "claude-judge", "ANTHROPIC_API_KEY": SECRET,
                                          **(env or {})}):
            out_dir, report = RUN_EVALS.run_suite(cases, runs, self.agent, judge, self.judge_info,
                                                  self.temp / "results", "reefstack", hidden={"ANTHROPIC_API_KEY"},
                                                  now=NOW)
        return out_dir, report, judge

    def test_packaged_suite_is_valid_and_blind(self):
        self.assertEqual(RUN_EVALS.validate_suite(), [])
        for required in ("web-ui-change-driven", "web-typo-no-launch", "web-launch-blocked",
                         "web-route-moved-updates-map", "cli-command-renamed-updates-map",
                         "review-flags-stale-map", "review-fix-refreshes-map"):
            self.assertIn(required, CASES)
        self.assertEqual({case["fixture"] for case in CASES.values()}, {"pantry", "tally"})

    def test_blinding_rejects_meta_words_in_prompts_names_and_files(self):
        fixtures = self.temp / "fixtures"
        shutil.copytree(ROOT / "evaluations/fixtures/tally", fixtures / "tally")
        case = {"id": "x", "fixture": "tally", "prompt": "Rename a command.", "rubric": ["ok"]}
        cases_path = self.temp / "cases.json"
        for change, expected in (({"prompt": "This eval checks a rename."}, "prompt reveals"),
                                 ({"project": "judge-sandbox"}, "project name reveals"),
                                 (None, "fixture file README.md reveals")):
            with self.subTest(expected=expected):
                if change is None:
                    (fixtures / "tally/README.md").write_text("Scored by a rubric.\n")
                cases_path.write_text(json.dumps({"runnable_cases": [{**case, **(change or {})}]}))
                problems = RUN_EVALS.validate_suite(cases_path, fixtures)
                self.assertTrue(any(expected in problem for problem in problems), problems)

    def test_workspace_is_a_neutral_committed_project(self):
        project, base, head = RUN_EVALS.prepare_workspace(CASES["review-flags-stale-map"],
                                                         ROOT / "evaluations/fixtures", self.temp / "work")
        self.assertEqual(project.name, "pantry")
        self.assertNotRegex(str(project.relative_to(self.temp)), r"evaluation|fixture|case")
        log = RUN_EVALS.git(project, "log", "--format=%s").splitlines()
        self.assertEqual(log, ["Serve the CSV download from /export/items.csv", "Initial commit"])
        self.assertNotEqual(base, head)
        self.assertIn("/items/export", (project / "docs/verification/items-export.md").read_text())
        project, _, _ = RUN_EVALS.prepare_workspace(CASES["cli-map-setup"], ROOT / "evaluations/fixtures",
                                                    self.temp / "other")
        self.assertFalse((project / "docs/verification").exists())

    def test_end_to_end_records_models_scores_reasons_and_artifacts(self):
        case = CASES["web-typo-no-launch"]
        out_dir, report, judge = self.suite([case], [verdict(case)])
        self.assertEqual(out_dir.name, "2026-10-10-reefstack")
        saved = json.loads((out_dir / "results.json").read_text())
        self.assertEqual(saved["date"], "2026-10-10T12:00:00+00:00")
        self.assertEqual((saved["agent"]["model"], saved["agent"]["family"]), ("gpt-6-luna", "openai"))
        self.assertEqual((saved["judge"]["model"], saved["judge"]["family"]), ("claude-judge", "anthropic"))
        result = saved["results"][0]
        self.assertEqual((result["score"], result["passed"]), (1.0, True))
        self.assertEqual(result["criteria"][0]["reason"], "seen in transcript")
        run_dir = out_dir / "cases/web-typo-no-launch/run-1"
        self.assertIn("+<thead><tr><th>Name</th><th>Quantity</th>", (run_dir / "diff.patch").read_text())
        transcript = (run_dir / "transcript.txt").read_text()
        self.assertIn("visible settings: []", transcript)
        self.assertIn("web-typo-no-launch", (out_dir / "summary.md").read_text())
        # The judge sees a neutral label, never the agent's model or the case id; the key is never written.
        self.assertNotIn("gpt-6-luna", judge.prompts[0])
        self.assertNotIn("web-typo-no-launch", judge.prompts[0])
        self.assertIn("Session: session-1", judge.prompts[0])
        for path in out_dir.rglob("*"):
            if path.is_file():
                self.assertNotIn(SECRET, path.read_text())

    def test_deterministic_checks_fail_a_case_the_judge_passed(self):
        case = CASES["web-route-moved-updates-map"]
        _, report, _ = self.suite([case], [verdict(case)])
        result = report["results"][0]
        self.assertFalse(result["checks"]["map_current"]["passed"])
        self.assertIn("items-export.md", result["checks"]["map_current"]["detail"])
        self.assertFalse(result["passed"])
        _, report, _ = self.suite([case], [verdict(case)], env={"FAKE_UPDATE_MAP": "1"})
        self.assertTrue(report["results"][0]["passed"], report["results"][0]["checks"])

    def test_transcript_that_finds_the_suite_fails_as_unblinded(self):
        case = copy.deepcopy(CASES["web-typo-no-launch"])
        case["prompt"] += " (see cases.json)"
        _, report, _ = self.suite([case], [verdict(case)])
        self.assertEqual(report["results"][0]["possible_unblinding"], ["cases.json"])
        self.assertFalse(report["results"][0]["passed"])

    def test_review_case_fails_when_the_agent_edits(self):
        case = copy.deepcopy(CASES["review-flags-stale-map"])
        case["prompt"] += " Also, is 'Quantitiy' spelled right?"
        _, report, _ = self.suite([case], [verdict(case)])
        self.assertFalse(report["results"][0]["checks"]["no_edits"]["passed"])

    def test_simulated_sandbox_denies_port_binding_for_the_agent(self):
        case = CASES["web-launch-blocked"]
        out_dir, report, _ = self.suite([case], [verdict(case, passed=False)])
        transcript = (out_dir / "cases/web-launch-blocked/run-1/transcript.txt").read_text()
        self.assertIn("bind failed: [Errno 1] Operation not permitted", transcript)
        self.assertEqual((report["results"][0]["score"], report["results"][0]["passed"]), (0.0, False))
        out_dir, _, _ = self.suite([CASES["web-typo-no-launch"]], [verdict(CASES["web-typo-no-launch"])])
        self.assertIn("bind ok", (out_dir / "cases/web-typo-no-launch/run-1/transcript.txt").read_text())

    def test_bad_judge_reply_is_a_failure_not_a_pass(self):
        case = CASES["web-typo-no-launch"]
        for reply in ("Looks great!", json.dumps({"criteria": [{"passed": True}]}),
                      RUN_EVALS.JudgeError("judge declined the request")):
            with self.subTest(reply=reply):
                _, report, _ = self.suite([case], [reply])
                result = report["results"][0]
                self.assertFalse(result["passed"])
                self.assertTrue(result["error"])

    def test_stopping_rule_needs_every_case_on_consecutive_runs(self):
        case = CASES["web-typo-no-launch"]
        _, report, _ = self.suite([case], [verdict(case), verdict(case)], runs=2)
        self.assertTrue(report["summary"]["stopping_rule_met"])
        _, report, _ = self.suite([case], [verdict(case), verdict(case, passed=False)], runs=2)
        self.assertFalse(report["summary"]["stopping_rule_met"])
        self.assertEqual(report["summary"]["cases"][case["id"]], {"passed_runs": 1, "runs": 2, "mean_score": 0.5})
        _, report, _ = self.suite([case], [verdict(case)], runs=1)
        self.assertTrue(report["summary"]["all_passed"])
        self.assertFalse(report["summary"]["stopping_rule_met"])

    def test_judge_configuration_comes_from_the_environment(self):
        with self.assertRaisesRegex(RUN_EVALS.SuiteError, "REEFSTACK_JUDGE_MODEL"):
            RUN_EVALS.judge_from_env({})
        with self.assertRaisesRegex(RUN_EVALS.SuiteError, "ANTHROPIC_API_KEY"):
            RUN_EVALS.judge_from_env({"REEFSTACK_JUDGE_MODEL": "claude-judge"})
        with self.assertRaisesRegex(RUN_EVALS.SuiteError, "unsupported"):
            RUN_EVALS.judge_from_env({"REEFSTACK_JUDGE_MODEL": "m", "REEFSTACK_JUDGE_PROVIDER": "other"})
        judge, info, hidden = RUN_EVALS.judge_from_env({"REEFSTACK_JUDGE_MODEL": "claude-judge",
                                                        "ANTHROPIC_API_KEY": SECRET})
        self.assertEqual((info, hidden), ({"provider": "anthropic", "model": "claude-judge"}, "ANTHROPIC_API_KEY"))
        self.assertNotIn(SECRET, json.dumps(info))

    def test_anthropic_judge_request_shape_and_refusal(self):
        sent = []

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def urlopen(request, timeout):
            sent.append(request)
            return Response(json.dumps(replies.pop(0)).encode())

        replies = [{"stop_reason": "end_turn", "content": [{"type": "text", "text": "{\"criteria\": []}"}]},
                   {"stop_reason": "refusal", "content": []}]
        judge = RUN_EVALS.AnthropicJudge("claude-judge", SECRET, urlopen=urlopen)
        self.assertEqual(judge("prompt"), "{\"criteria\": []}")
        request = sent[0]
        self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(request.get_header("X-api-key"), SECRET)
        self.assertEqual(request.get_header("Anthropic-version"), "2023-06-01")
        body = json.loads(request.data)
        self.assertEqual((body["model"], body["messages"][0]["content"]), ("claude-judge", "prompt"))
        with self.assertRaisesRegex(RUN_EVALS.JudgeError, "declined"):
            judge("prompt")

    def test_command_judge_and_cli_transport(self):
        case = CASES["web-typo-no-launch"]
        judge_script = self.temp / "judge.py"
        judge_script.write_text("import sys\nsys.stdin.read()\nprint(" + repr(verdict(case)) + ")\n")
        env = {**os.environ, "REEFSTACK_JUDGE_PROVIDER": "command", "REEFSTACK_JUDGE_MODEL": "claude-judge",
               "REEFSTACK_JUDGE_COMMAND": f'"{sys.executable}" "{judge_script}"'}
        command = [sys.executable, str(ROOT / "scripts/run_evals.py"), "--case", case["id"],
                   "--agent-model", "gpt-6-luna", "--agent-command", self.agent["command"],
                   "--results", str(self.temp / "cli results")]
        run = subprocess.run(command, text=True, capture_output=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("1 of 1 case runs passed; stopping rule not met", run.stdout)
        same_family = subprocess.run(command[:-2] + ["--results", str(self.temp / "r2")], text=True,
                                     capture_output=True, env={**env, "REEFSTACK_JUDGE_MODEL": "gpt-6-astra"})
        self.assertEqual(same_family.returncode, 2)
        self.assertIn("both openai models", same_family.stderr)
        self.assertFalse((self.temp / "r2").exists())

    def test_model_families(self):
        for model, family in (("gpt-6.1-sol", "openai"), ("claude-judge", "anthropic"), ("o4-mini", "openai"),
                              ("gemini-3-pro", "google"), ("vendor/claude-x", "anthropic"), ("mystery", "unknown")):
            self.assertEqual(RUN_EVALS.model_family(model), family)

    def test_fixture_apps_pass_their_own_checks(self):
        for fixture in ("pantry", "tally"):
            with self.subTest(fixture=fixture), tempfile.TemporaryDirectory() as parent:
                copy_dir = Path(parent) / fixture
                shutil.copytree(ROOT / "evaluations/fixtures" / fixture, copy_dir)
                run = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=copy_dir,
                                     text=True, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
