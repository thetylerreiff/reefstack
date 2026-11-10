import copy
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
import zipfile


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
    skill = pathlib.Path(".agents/skills/reefstack/SKILL.md")
    if skill.exists():
        print("read", skill.resolve())
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


def running(pid):
    """True while the process exists and is not a zombie awaiting its parent."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    return not (stat.exists() and stat.read_text().rsplit(")", 1)[1].split()[0] == "Z")


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
                      "model": "gpt-test-agent", "timeout": 60}
        self.judge_info = {"provider": "anthropic", "model": "claude-judge"}

    def tearDown(self):
        self.directory.cleanup()

    def suite(self, cases, replies, runs=1, env=None, full_suite=True, committed=True, arm="host"):
        judge = MockJudge(replies)
        state = {"version": "0.0.0", "revision": "abc1234", "uncommitted_procedure_changes": not committed,
                 "installation_in_agent": "not_checked"}
        with mock.patch.dict(os.environ, {"REEFSTACK_JUDGE_MODEL": "claude-judge", "ANTHROPIC_API_KEY": SECRET,
                                          **(env or {})}), mock.patch.object(RUN_EVALS, "plugin_state",
                                                                            return_value=state):
            out_dir, report = RUN_EVALS.run_suite(cases, runs, self.agent, judge, self.judge_info,
                                                  self.temp / "results", "reefstack", hidden={"ANTHROPIC_API_KEY"},
                                                  now=NOW, full_suite=full_suite, arm=arm)
        return out_dir, report, judge

    def test_arms_put_skills_in_the_project_but_out_of_its_history(self):
        case = CASES["web-typo-no-launch"]
        for arm in RUN_EVALS.ARMS:
            with self.subTest(arm=arm), tempfile.TemporaryDirectory() as parent:
                project, _, _ = RUN_EVALS.prepare_workspace(case, RUN_EVALS.EVALUATIONS / "fixtures", parent, arm)
                installed = (project / ".agents/skills/reefstack/SKILL.md").is_file()
                self.assertEqual(installed, arm.startswith("reefstack"))
                self.assertEqual(installed, (project / ".agents/skills/map/scripts/map_lint.py").is_file())
                named = (project / "AGENTS.md").read_text() if (project / "AGENTS.md").exists() else ""
                self.assertEqual("use the reefstack skill" in named, arm == "reefstack-named")
                # Neither the skills nor the instruction line count as the agent's edits.
                self.assertEqual(RUN_EVALS.git(project, "status", "--porcelain"), "")
                self.assertEqual(RUN_EVALS.capture_diff(project, "HEAD"), "")
                self.assertNotIn(".agents", RUN_EVALS.git(project, "ls-files"))

    def test_trigger_rate_counts_sessions_that_name_the_coordinator(self):
        case = CASES["web-typo-no-launch"]
        for arm, read in (("reefstack", True), ("reefstack-named", True), ("plain", False), ("host", False)):
            with self.subTest(arm=arm):
                out_dir, report, _ = self.suite([case], [verdict(case), verdict(case)], runs=2, arm=arm)
                self.assertEqual([item["coordinator_read"] for item in report["results"]], [read, read])
                self.assertEqual((report["summary"]["coordinator_read_runs"], report["summary"]["trigger_rate"]),
                                 (2 * read, float(read)))
                self.assertEqual(report["arm"], arm)
                self.assertTrue(report["summary"]["all_passed"])
                self.assertIn(f"Arm: {arm}. Coordinator skill named in {2 * read} of 2 sessions",
                              (out_dir / "summary.md").read_text())
        self.assertEqual(report["reefstack"]["installation_in_agent"], "not_checked")
        _, report, _ = self.suite([case], [verdict(case)], arm="reefstack")
        self.assertEqual(report["reefstack"]["installation_in_agent"], "project_skills")
        # A mention of some other skill, or of the folder alone, is not a read of the coordinator.
        for text in ("cat .agents/skills/grill/SKILL.md", "ls .agents/skills/reefstack", "my-reefstack/SKILL.md"):
            self.assertIsNone(RUN_EVALS.COORDINATOR_READ.search(text), text)
        self.assertTrue(RUN_EVALS.COORDINATOR_READ.search("sed -n 1,80p /home/u/.agents/skills/reefstack/SKILL.md"))

    def test_procedure_use_reads_playbooks_and_the_final_step_trace_from_the_transcript(self):
        trace = "Playbook: feature\n" + "\n".join(f"{n}. {name}: done" for n, name in enumerate(
            ("acceptance", "contract", "workstream", "change", "evidence", "findings"), 1))
        lines = [{"type": "item.completed", "item": {"type": "command_execution", "command":
                  "cat .agents/skills/reefstack/references/playbooks/feature.md "
                  ".agents/skills/reefstack/references/playbooks/graph.md"}},
                 {"type": "item.completed", "item": {"type": "agent_message", "text": "Playbook: nonsense"}},
                 {"type": "item.completed", "item": {"type": "agent_message", "text": "Done.\n" + trace}}]
        use = RUN_EVALS.procedure_use("\n".join(json.dumps(line) for line in lines) + "\nnot json")
        self.assertEqual(use, {"playbooks_read": ["feature"],
                               "step_trace": {"playbook": "feature", "valid": True, "errors": []}})
        broken = RUN_EVALS.procedure_use(trace.replace("3. workstream: done\n", ""))["step_trace"]
        self.assertFalse(broken["valid"])
        self.assertIn("step 3 is missing", " ".join(broken["errors"]))
        # A report with no trace is recorded as such, not as an error: small edits follow no playbook.
        self.assertEqual(RUN_EVALS.procedure_use("Fixed the typo.")["step_trace"],
                         {"playbook": None, "valid": False, "errors": []})

    def test_plain_arm_that_loaded_the_coordinator_is_reported_as_not_a_baseline(self):
        case = copy.deepcopy(CASES["web-typo-no-launch"])
        case["prompt"] += " (I already read plugins/reefstack/skills/reefstack/SKILL.md)"
        out_dir, report, _ = self.suite([case], [verdict(case)], arm="plain")
        self.assertEqual(report["summary"]["coordinator_read_runs"], 1)
        self.assertIn("the arm is not a baseline", (out_dir / "summary.md").read_text())

    def test_a_suite_file_the_skills_name_is_skipped_as_a_probe_and_recorded(self):
        # The coordinator itself names evaluations/playbook.md, so reading it must not fail a run as unblinded.
        case = copy.deepcopy(CASES["web-typo-no-launch"])
        case["prompt"] += " (see evaluations/playbook.md)"
        _, report, _ = self.suite([case], [verdict(case)])
        result = report["results"][0]
        self.assertEqual((result["possible_unblinding"], result["unblinding_probes_skipped"]), ([], ["playbook.md"]))
        self.assertTrue(result["passed"])

    def test_installing_arms_refuse_a_host_that_already_has_reefstack(self):
        home = self.temp / "home"
        (home / ".agents/skills/reefstack").mkdir(parents=True)
        env = {"REEFSTACK_JUDGE_MODEL": "claude-judge", "ANTHROPIC_API_KEY": SECRET}
        with mock.patch.dict(os.environ, env), mock.patch.object(RUN_EVALS.Path, "home", return_value=home), \
                mock.patch.object(RUN_EVALS, "run_suite", return_value=("out", {})) as run_suite:
            parser_args = dict(case=["web-typo-no-launch"], runs=1, agent_model="gpt-test-agent",
                               agent_command="true", timeout=5, results=str(self.temp / "r"), label=None)
            for arm in ("plain", "reefstack", "reefstack-named"):
                with self.subTest(arm=arm), self.assertRaisesRegex(RUN_EVALS.SuiteError, "host without Reefstack"):
                    RUN_EVALS.run_new(mock.Mock(arm=arm, **parser_args), list(CASES.values()))
            run_suite.assert_not_called()
            RUN_EVALS.run_new(mock.Mock(arm="host", **parser_args), list(CASES.values()))
            self.assertEqual((run_suite.call_args.args[6], run_suite.call_args.kwargs["arm"]), ("host", "host"))

    def test_packaged_suite_is_valid_and_blind(self):
        self.assertEqual(RUN_EVALS.validate_suite(), [])
        for required in ("web-ui-change-driven", "web-typo-no-launch", "web-launch-blocked",
                         "web-route-moved-updates-map", "cli-command-renamed-updates-map",
                         "review-flags-stale-map", "review-fix-refreshes-map",
                         "workflow-substantial-import", "workflow-resume-new-constraint",
                         "workflow-read-only-pickup", "playbook-refactor-preserves-behavior",
                         "playbook-performance-measured", "playbook-prototype-disposable"):
            self.assertIn(required, CASES)
        self.assertEqual({case["fixture"] for case in CASES.values()}, {"pantry", "tally", "dispatch"})

    def test_live_trial_map_mistakes_fail_until_repaired(self):
        # Replay the two actual map defects from the import and resume probes.
        # The app may work; neither defect should pass the workflow check.
        case = CASES["workflow-resume-new-constraint"]
        project, base, head = RUN_EVALS.prepare_workspace(
            case, ROOT / "evaluations/fixtures", self.temp)
        feature = project / "docs/verification/category-totals.md"
        original = feature.read_text()
        alias_map = original.replace(
            "- cli: `python3 -m tally summary`",
            "- cli: `python3 -m tally report`\n"
            "- cli alias: `python3 -m tally summary` (identical output)")
        self.assertNotEqual(alias_map, original)
        feature.write_text(alias_map)
        checks = RUN_EVALS.run_checks(case, project, base, head)
        self.assertFalse(checks["map_lint"]["passed"])
        self.assertIn("write entry points", checks["map_lint"]["detail"])
        feature.write_text(alias_map.replace("- cli alias:", "- cli:"))
        self.assertTrue(RUN_EVALS.run_checks(case, project, base, head)["map_lint"]["passed"])

        repaired = feature.read_text()
        feature.write_text(repaired.replace("## What it is\n", ""))
        checks = RUN_EVALS.run_checks(case, project, base, head)
        self.assertFalse(checks["map_lint"]["passed"])
        self.assertIn("missing section(s) ## What it is", checks["map_lint"]["detail"])
        feature.write_text(repaired)
        self.assertTrue(RUN_EVALS.run_checks(case, project, base, head)["map_lint"]["passed"])


    def test_import_case_requires_new_command_coverage_not_just_valid_shape(self):
        case = CASES["workflow-substantial-import"]
        project, base, head = RUN_EVALS.prepare_workspace(
            case, ROOT / "evaluations/fixtures", self.temp)
        checks = RUN_EVALS.run_checks(case, project, base, head)
        self.assertTrue(checks["map_lint"]["passed"])
        self.assertFalse(checks["import_map_entry"]["passed"])
        feature = project / "docs/verification/category-totals.md"
        original = feature.read_text()
        for decoy in ("\n`tally import file.csv`\n", "\n- cli: `tally import file.csv`\n"):
            feature.write_text(original + decoy)
            self.assertFalse(RUN_EVALS.run_checks(case, project, base, head)["import_map_entry"]["passed"])
        feature.write_text(original.replace(
            "## How to reach it\n", "## How to reach it\n\n- cli: `python3 -m tally import expenses.csv`\n"))
        checks = RUN_EVALS.run_checks(case, project, base, head)
        self.assertTrue(checks["map_lint"]["passed"])
        self.assertTrue(checks["import_map_entry"]["passed"])


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
        self.assertTrue((project / ".gitignore").is_file())
        self.assertFalse((project / "gitignore").exists())
        project, _, _ = RUN_EVALS.prepare_workspace(CASES["cli-map-setup"], ROOT / "evaluations/fixtures",
                                                    self.temp / "other")
        self.assertFalse((project / "docs/verification").exists())

    def test_procedure_cases_start_from_runnable_unmodified_dispatch_project(self):
        for name in ("playbook-refactor-preserves-behavior", "playbook-performance-measured",
                     "playbook-prototype-disposable"):
            with self.subTest(case=name):
                project, base, head = RUN_EVALS.prepare_workspace(
                    CASES[name], ROOT / "evaluations/fixtures", self.temp / name)
                self.assertEqual(base, head)
                self.assertEqual(project.name, "dispatch")
                self.assertFalse((project / "scratch").exists())
                # The only tests visible to the agent are the ordinary project's
                # checks; the outer acceptance suite and criteria are held out.
                self.assertFalse((project / "test_playbook_behavior.py").exists())
                env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
                result = subprocess.run([sys.executable, "-m", "unittest", "-v"],
                                        cwd=project, env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(RUN_EVALS.git(project, "status", "--porcelain"), "")
                self.assertEqual(RUN_EVALS.run_checks(CASES[name], project, base, head), {})

    def test_workflow_handoff_is_applied_to_a_real_git_project(self):
        for name in ("workflow-resume-new-constraint", "workflow-read-only-pickup"):
            with self.subTest(case=name):
                case = CASES[name]
                project, base, head = RUN_EVALS.prepare_workspace(
                    case, ROOT / "evaluations/fixtures", self.temp / name)
                self.assertNotEqual(base, head)
                self.assertEqual(RUN_EVALS.git(project, "status", "--porcelain"), "")
                note = project / "docs/plans/report-command.md"
                self.assertTrue(note.is_file())
                self.assertIn("in its own checkout", note.read_text())
                self.assertIn('run_cli("summary")', (project / "test_tally.py").read_text())
                env = {**os.environ, "TALLY_HOME": str(self.temp / (name + "-data"))}
                for args, status in ((("add", "12.25", "food"), 0), (("report",), 0),
                                     (("summary",), 2)):
                    result = subprocess.run([sys.executable, "-m", "tally", *args], cwd=project,
                                            env=env, text=True, capture_output=True)
                    self.assertEqual(result.returncode, status, result.stderr)
                    if args == ("report",):
                        self.assertEqual(result.stdout.splitlines()[-1].split(), ["total", "12.25"])
                # This is genuinely incomplete integration, not merely stale prose.
                result = subprocess.run([sys.executable, "-m", "unittest"], cwd=project,
                                        env=env, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("test_summary_totals_per_category", result.stderr)
                check = {"checks": ["no_edits"]}
                self.assertTrue(RUN_EVALS.run_checks(check, project, base, head)["no_edits"]["passed"])
                note.write_text(note.read_text() + "\nAll done.\n")
                self.assertFalse(RUN_EVALS.run_checks(check, project, base, head)["no_edits"]["passed"])

    def test_no_edits_rejects_staged_untracked_and_committed_handoff_changes(self):
        for change in ("staged", "untracked", "committed"):
            with self.subTest(change=change):
                case = CASES["workflow-read-only-pickup"]
                project, base, head = RUN_EVALS.prepare_workspace(
                    case, ROOT / "evaluations/fixtures", self.temp / change)
                note = project / "docs/plans/next.md"
                note.write_text("Next: finish command integration.\n")
                if change != "untracked":
                    RUN_EVALS.git(project, "add", "-A")
                if change == "committed":
                    RUN_EVALS.git(project, "commit", "-q", "-m", "Note next step")
                result = RUN_EVALS.run_checks(case, project, base, head)["no_edits"]
                self.assertFalse(result["passed"])
                self.assertIn("new commits" if change == "committed" else "working tree changed",
                              result["detail"])

    def test_workflow_patches_survive_release_packaging_and_stay_blind(self):
        package = RUN_EVALS.load_module("workflow_package", ROOT / "scripts/package.py")
        archive_path = self.temp / "plugin.zip"
        package.build_archive(archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            self.assertIn("reefstack/evaluations/fixtures/patches/workflow-report-handoff.patch",
                          archive.namelist())
            archive.extractall(self.temp / "release")
        release = self.temp / "release/reefstack"
        runner = RUN_EVALS.load_module("packaged_workflow_runner", release / "scripts/run_evals.py")
        self.assertEqual(runner.validate_suite(), [])
        cases = {case["id"]: case for case in runner.load_cases()}
        case = cases["workflow-read-only-pickup"]
        project, base, head = runner.prepare_workspace(case, release / "evaluations/fixtures",
                                                      self.temp / "from-release")
        self.assertTrue((project / "docs/plans/report-command.md").is_file())
        self.assertTrue(runner.run_checks(case, project, base, head)["no_edits"]["passed"])

    def test_end_to_end_records_models_scores_reasons_and_artifacts(self):
        case = CASES["web-typo-no-launch"]
        out_dir, report, judge = self.suite([case], [verdict(case)])
        self.assertEqual(out_dir.name, "2026-10-10-reefstack")
        saved = json.loads((out_dir / "results.json").read_text())
        self.assertEqual(saved["date"], "2026-10-10T12:00:00+00:00")
        self.assertEqual((saved["agent"]["model"], saved["agent"]["family"]), ("gpt-test-agent", "openai"))
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
        self.assertNotIn("gpt-test-agent", judge.prompts[0])
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
        # A subset of the suite, or procedures with uncommitted edits, never meets the rule.
        _, report, _ = self.suite([case], [verdict(case), verdict(case)], runs=2, full_suite=False)
        self.assertFalse(report["summary"]["stopping_rule_met"])
        _, report, _ = self.suite([case], [verdict(case), verdict(case)], runs=2, committed=False)
        self.assertFalse(report["summary"]["stopping_rule_met"])

    def test_agent_exit_failure_and_leftover_servers(self):
        case = CASES["web-typo-no-launch"]
        script = self.temp / "server_agent.py"
        script.write_text(textwrap.dedent('''
            import subprocess, sys
            sys.stdin.read()
            server = subprocess.Popen(["sleep", "60"])
            open(sys.argv[1], "w").write(str(server.pid))
            print("started server; pwd", __import__("os").environ.get("PWD"), "oldpwd",
                  __import__("os").environ.get("OLDPWD"))
            sys.exit(int(sys.argv[2]))
        '''))
        pid_file = self.temp / "server.pid"
        self.agent["command"] = f'"{sys.executable}" "{script}" "{pid_file}" 3'
        started = __import__("time").monotonic()
        out_dir, report, _ = self.suite([case], [verdict(case)])
        self.assertLess(__import__("time").monotonic() - started, 20)
        result = report["results"][0]
        self.assertEqual(result["agent_exit"], 3)
        self.assertFalse(result["passed"])
        self.assertFalse(running(int(pid_file.read_text())))
        transcript = (out_dir / "cases/web-typo-no-launch/run-1/transcript.txt").read_text()
        self.assertRegex(transcript, r"pwd \S+/pantry oldpwd None")

    def test_port_denial_traceback_does_not_point_at_an_injected_file(self):
        case = CASES["web-launch-blocked"]
        project = self.temp / "pantry"
        project.mkdir()
        env = RUN_EVALS.agent_environment(case, self.temp / "scratch", project)
        run = subprocess.run([sys.executable, "-c", "import socket; socket.socket().bind(('127.0.0.1', 0))"],
                             env=env, text=True, capture_output=True)
        self.assertIn("PermissionError: [Errno 1] Operation not permitted", run.stderr)
        self.assertIn("<frozen socket>", run.stderr)
        self.assertNotIn("sitecustomize", run.stderr)

    def test_probing_the_simulated_sandbox_is_flagged(self):
        case = copy.deepcopy(CASES["web-launch-blocked"])
        case["prompt"] += " Check PYTHONPATH first."
        _, report, _ = self.suite([case], [verdict(case)])
        self.assertEqual(report["results"][0]["possible_unblinding"], ["PYTHONPATH"])

    def test_oversized_judge_inputs_are_cut_and_recorded(self):
        case = CASES["web-typo-no-launch"]
        prompt, truncated = RUN_EVALS.judge_prompt(case, "session-1", "x" * 400_000, "d" * 10, {})
        self.assertEqual(truncated, ["transcript"])
        self.assertLess(len(prompt), 310_000)
        self.assertIn("characters omitted", prompt)

    def test_rejudge_scores_saved_sessions_without_the_agent(self):
        case = CASES["web-typo-no-launch"]
        out_dir, report, _ = self.suite([case], [RUN_EVALS.JudgeError("HTTP 529")])
        self.assertFalse(report["results"][0]["passed"])
        report = RUN_EVALS.rejudge(out_dir, MockJudge([verdict(case)]), self.judge_info, list(CASES.values()))
        self.assertTrue(report["results"][0]["passed"])
        self.assertTrue(json.loads((out_dir / "results.json").read_text())["results"][0]["passed"])
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
        self.assertEqual((info, hidden), ({"provider": "anthropic", "model": "claude-judge"}, {"ANTHROPIC_API_KEY"}))
        _, _, hidden = RUN_EVALS.judge_from_env({"REEFSTACK_JUDGE_MODEL": "gemini-x", "REEFSTACK_JUDGE_PROVIDER":
                                                 "command", "REEFSTACK_JUDGE_COMMAND": "judge",
                                                 "REEFSTACK_JUDGE_SECRET_ENV": "GEMINI_API_KEY, OTHER"})
        self.assertEqual(hidden, {"GEMINI_API_KEY", "OTHER"})
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
            reply = replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return Response(json.dumps(reply).encode())

        def overloaded(code):
            return RUN_EVALS.urllib.error.HTTPError("u", code, "busy", {}, io.BytesIO(b"busy"))

        replies = [overloaded(529), {"stop_reason": "end_turn", "content": [{"type": "text", "text": "{\"criteria\": []}"}]},
                   {"stop_reason": "refusal", "content": []}, overloaded(400)]
        waits = []
        judge = RUN_EVALS.AnthropicJudge("claude-judge", SECRET, urlopen=urlopen, sleep=waits.append)
        self.assertEqual(judge("prompt"), "{\"criteria\": []}")
        request = sent[0]
        self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(request.get_header("X-api-key"), SECRET)
        self.assertEqual(request.get_header("Anthropic-version"), "2023-06-01")
        body = json.loads(request.data)
        self.assertEqual((body["model"], body["messages"][0]["content"]), ("claude-judge", "prompt"))
        self.assertEqual(waits, [2])
        with self.assertRaisesRegex(RUN_EVALS.JudgeError, "declined"):
            judge("prompt")
        with self.assertRaisesRegex(RUN_EVALS.JudgeError, "HTTP 400"):
            judge("prompt")
        self.assertEqual(waits, [2])

    def test_project_trust_is_scoped_and_transported_as_one_literal_argument(self):
        project = self.temp / 'Project "x" $(touch NOT_CREATED) {model}'
        project.mkdir()
        script = self.temp / "argv.py"
        script.write_text("import json,sys\nsys.stdin.read()\nprint(json.dumps(sys.argv[1:]))\n")
        command = shlex.join([sys.executable, str(script), "-c", "{project_trust}", "{model}"])
        output, status, _ = RUN_EVALS.run_agent(command, "test-model", "hi", project, dict(os.environ), 10)
        self.assertEqual(status, 0)
        args = json.loads(output)
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], "-c")
        self.assertEqual(args[2], "test-model")
        self.assertEqual(args[1], "projects={" + json.dumps(str(project.resolve())) + '={trust_level="trusted"}}')
        self.assertFalse((project / "NOT_CREATED").exists())
        defaults = shlex.split(RUN_EVALS.DEFAULT_AGENT_COMMAND)
        self.assertEqual(defaults[defaults.index("-c") + 1], "{project_trust}")

    def test_command_judge_and_cli_transport(self):
        case = CASES["web-typo-no-launch"]
        judge_script = self.temp / "judge.py"
        judge_script.write_text("import sys\nsys.stdin.read()\nprint(" + repr(verdict(case)) + ")\n")
        env = {**os.environ, "REEFSTACK_JUDGE_PROVIDER": "command", "REEFSTACK_JUDGE_MODEL": "claude-judge",
               "REEFSTACK_JUDGE_COMMAND": f'"{sys.executable}" "{judge_script}"'}
        command = [sys.executable, str(ROOT / "scripts/run_evals.py"), "--case", case["id"],
                   "--agent-model", "gpt-test-agent", "--agent-command", self.agent["command"],
                   "--results", str(self.temp / "cli results")]
        run = subprocess.run(command, text=True, capture_output=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("1 of 1 case runs passed; stopping rule not met", run.stdout)
        same_family = subprocess.run(command[:-2] + ["--results", str(self.temp / "r2")], text=True,
                                     capture_output=True, env={**env, "REEFSTACK_JUDGE_MODEL": "gpt-test-judge"})
        self.assertEqual(same_family.returncode, 2)
        self.assertIn("both openai models", same_family.stderr)
        self.assertFalse((self.temp / "r2").exists())

    def test_model_families(self):
        for model, family in (("gpt-test-model", "openai"), ("claude-judge", "anthropic"), ("o4-mini", "openai"),
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
