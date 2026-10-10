#!/usr/bin/env python3
"""Run Reefstack's runnable cases against a coding agent and a blind judge on another model family."""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
EVALUATIONS = ROOT / "evaluations"
CHECKS = ("map_lint", "map_current", "no_edits")
SETUP_KEYS = {"patches", "remove", "deny_port_binding"}
# Words that tell the agent it is being measured. "test" stays allowed: real apps have tests and
# real users ask to test their app.
META_WORDS = re.compile(r"(?i)\b(evals?|evaluat\w*|judg\w*|rubrics?|scor(?:e|es|ed|ing)|benchmark\w*|"
                        r"candidates?|arena|experiment\w*|grad(?:er|ers|ing|ed))\b")
# Files that would tell the agent about the run if it found them in the installed plugin.
SUITE_FILES = ("cases.json", "playbook.md", "run_evals.py")
# Signs that the agent went looking at the simulated port denial instead of reporting it.
SANDBOX_PROBES = ("PYTHONPATH", "sitecustomize")
DEFAULT_AGENT_COMMAND = "codex exec --json --full-auto --skip-git-repo-check -m {model} -"
FAMILIES = (("anthropic", r"claude"), ("openai", r"gpt|o\d|codex|chatgpt"), ("google", r"gemini|gemma"),
            ("meta", r"llama"), ("mistral", r"mistral|codestral"), ("xai", r"grok"), ("deepseek", r"deepseek"))
GIT_IDENTITY = {"GIT_AUTHOR_NAME": "Sam Rivera", "GIT_AUTHOR_EMAIL": "sam@example.test",
                "GIT_COMMITTER_NAME": "Sam Rivera", "GIT_COMMITTER_EMAIL": "sam@example.test"}
# Simulates a sandbox that refuses local ports for Python processes. Compiled under a stdlib-looking
# name so a traceback does not point at an injected file.
DENY_BIND = '''exec(compile("""
import errno
import socket

_bind = socket.socket.bind


def bind(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        raise PermissionError(errno.EPERM, "Operation not permitted")
    return _bind(self, address)


socket.socket.bind = bind
""", "<frozen socket>", "exec"))
'''
# Judge inputs above these sizes are cut in the middle, and the result records it.
MAX_TRANSCRIPT_CHARS = 300_000
MAX_DIFF_CHARS = 200_000
RETRY_STATUSES = {408, 429, 500, 502, 503, 504, 529}
JUDGE_INSTRUCTIONS = """You are reviewing one coding-agent session. A user gave the agent the request below in a small
project. You see the session transcript, the final diff, and automatic check results. Decide each criterion
independently from that evidence only: claims in the transcript are not proof unless the transcript also shows
the command, output, or file that backs them. When evidence is missing, the criterion fails.

Reply with only a JSON object:
{"criteria": [{"criterion": "<copied text>", "passed": true or false, "reason": "<one or two sentences citing evidence>"}],
 "summary": "<two sentences>"}
Return one entry per criterion, in the given order."""


class SuiteError(ValueError):
    """The case file, a fixture, or the run configuration is unusable."""


class JudgeError(RuntimeError):
    """The judge could not produce a usable verdict."""


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MAP_LINT = load_module("reefstack_map_lint", ROOT / "scripts/map_lint.py")


def load_cases(path=EVALUATIONS / "cases.json"):
    return json.loads(Path(path).read_text(encoding="utf-8")).get("runnable_cases", [])


def visible_text(case, fixtures):
    """Every name and text the agent can see in its workspace or prompt, as (where, text) pairs."""
    yield "prompt", case.get("prompt", "")
    yield "project name", case.get("project", case.get("fixture", ""))
    fixture = Path(fixtures) / case.get("fixture", "")
    for path in sorted(fixture.rglob("*")) if fixture.is_dir() else ():
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(fixture).as_posix()
        yield "fixture path " + relative, relative
        if path.is_file():
            yield "fixture file " + relative, path.read_text(encoding="utf-8", errors="ignore")
    for patch in case.get("setup", {}).get("patches", []):
        yield "commit message", patch.get("message", "")
        source = Path(fixtures) / patch.get("file", "")
        if source.is_file():
            yield "patch " + patch["file"], source.read_text(encoding="utf-8", errors="ignore")


def validate_suite(cases_path=EVALUATIONS / "cases.json", fixtures=EVALUATIONS / "fixtures"):
    """Return a list of problems with the runnable cases; an empty list means the suite is usable."""
    try:
        cases = load_cases(cases_path)
    except (OSError, ValueError) as error:
        return [f"cannot read cases: {error}"]
    problems, seen = [], set()
    if not cases:
        problems.append("no runnable_cases")
    for case in cases:
        name = case.get("id", "<missing id>")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or name in seen:
            problems.append(f"{name}: id must be unique and lowercase-hyphenated")
        seen.add(name)
        if not case.get("fixture") or not (Path(fixtures) / case["fixture"]).is_dir():
            problems.append(f"{name}: fixture '{case.get('fixture')}' not found under {fixtures}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            problems.append(f"{name}: needs a prompt")
        rubric = case.get("rubric")
        if not isinstance(rubric, list) or not rubric or not all(isinstance(item, str) and item.strip()
                                                                for item in rubric):
            problems.append(f"{name}: rubric must be a non-empty list of criteria")
        if set(case.get("checks", [])) - set(CHECKS):
            problems.append(f"{name}: unknown checks {sorted(set(case['checks']) - set(CHECKS))}")
        setup = case.get("setup", {})
        if set(setup) - SETUP_KEYS:
            problems.append(f"{name}: unknown setup keys {sorted(set(setup) - SETUP_KEYS)}")
        for patch in setup.get("patches", []):
            if not (Path(fixtures) / patch.get("file", "")).is_file() or not patch.get("message"):
                problems.append(f"{name}: patch needs an existing file and a commit message")
        for where, text in visible_text(case, fixtures):
            match = META_WORDS.search(text)
            if match:
                problems.append(f"{name}: {where} reveals the run is measured ('{match.group()}'); reword it")
    return problems


def model_family(model):
    name = (model or "").lower().split("/")[-1]
    for family, pattern in FAMILIES:
        if re.match(pattern, name):
            return family
    return "unknown"


def git(project, *args, env=None):
    run = subprocess.run(["git", "-C", str(project), *args], text=True, capture_output=True,
                         env={**os.environ, **GIT_IDENTITY, **(env or {})})
    if run.returncode:
        raise SuiteError("git " + " ".join(args) + " failed: " + run.stderr.strip())
    return run.stdout


def prepare_workspace(case, fixtures, parent):
    """Copy the fixture into a neutrally named project and commit it; return (project, base, head)."""
    project = Path(parent) / case.get("project", case["fixture"])
    shutil.copytree(Path(fixtures) / case["fixture"], project,
                    ignore=shutil.ignore_patterns("__pycache__", "data"))
    # Fixtures keep ignore files as "gitignore" because release archives drop dotfiles.
    for ignore in project.rglob("gitignore"):
        ignore.rename(ignore.with_name(".gitignore"))
    setup = case.get("setup", {})
    for relative in setup.get("remove", []):
        target = project / relative
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    git(project, "init", "-q")
    git(project, "symbolic-ref", "HEAD", "refs/heads/main")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "Initial commit")
    base = git(project, "rev-parse", "HEAD").strip()
    for patch in setup.get("patches", []):
        git(project, "apply", str((Path(fixtures) / patch["file"]).resolve()))
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", patch["message"])
    return project, base, git(project, "rev-parse", "HEAD").strip()


def agent_environment(case, scratch, project, hidden=()):
    """The agent's environment: no runner or judge settings, plus any simulated sandbox limits."""
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("REEFSTACK_") and key not in hidden and key != "OLDPWD"}
    env["PWD"] = str(project)
    if case.get("setup", {}).get("deny_port_binding"):
        site = Path(scratch) / "lib"
        site.mkdir(parents=True, exist_ok=True)
        (site / "sitecustomize.py").write_text(DENY_BIND)
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(site), env.get("PYTHONPATH")]))
    return env


def stop_group(process):
    """Stop everything the agent started, including background servers, by process group."""
    if not hasattr(os, "killpg"):
        process.kill()
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except (ProcessLookupError, PermissionError):
            return
        time.sleep(0.5)


def run_agent(command, model, prompt, project, env, timeout):
    argv = [part.replace("{model}", model) for part in shlex.split(command)]
    started = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            # Output goes to files, not pipes, so a server the agent left running cannot hold the runner.
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, cwd=project,
                                       env=env, start_new_session=hasattr(os, "killpg"))
        except OSError as error:
            raise SuiteError(f"cannot start agent command {argv[0]!r}: {error}")
        try:
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
        except OSError:
            pass
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            status = "timeout"
        stop_group(process)
        process.wait()
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
    transcript = out + ("\n--- stderr ---\n" + err if err else "")
    return transcript, status, round(time.monotonic() - started, 1)


def run_checks(case, project, base, head):
    results = {}
    for name in case.get("checks", []):
        try:
            if name == "map_lint":
                errors = MAP_LINT.lint_directory(project / "docs/verification")
            elif name == "map_current":
                directory = project / "docs/verification"
                errors = MAP_LINT.stale_entries(directory, base) if directory.is_dir() else ["no map"]
            else:
                changed = git(project, "status", "--porcelain").strip()
                moved = git(project, "rev-parse", "HEAD").strip() != head
                errors = (["working tree changed"] if changed else []) + (["new commits"] if moved else [])
        except (OSError, ValueError) as error:
            errors = [str(error)]
        results[name] = {"passed": not errors, "detail": "; ".join(errors) or "ok"}
    return results


def capture_diff(project, base):
    git(project, "add", "-A")
    return git(project, "diff", "--cached", "--no-color", base)


def clip(text, limit):
    if len(text) <= limit:
        return text, False
    half = limit // 2
    return text[:half] + f"\n[... {len(text) - limit} characters omitted ...]\n" + text[-half:], True


def judge_prompt(case, label, transcript, diff, checks):
    """Return the judge prompt and which inputs were cut to fit."""
    transcript, cut_transcript = clip(transcript, MAX_TRANSCRIPT_CHARS)
    diff, cut_diff = clip(diff, MAX_DIFF_CHARS)
    truncated = [name for name, cut in (("transcript", cut_transcript), ("diff", cut_diff)) if cut]
    criteria = "\n".join(f"{index}. {item}" for index, item in enumerate(case["rubric"], 1))
    return "\n\n".join([
        JUDGE_INSTRUCTIONS,
        f"Session: {label}",
        "User request:\n" + case["prompt"],
        "Criteria:\n" + criteria,
        "Automatic checks:\n" + json.dumps(checks, indent=2),
        "Transcript:\n<transcript>\n" + transcript + "\n</transcript>",
        "Final diff against the starting commit:\n<diff>\n" + (diff or "(no changes)") + "\n</diff>",
    ]), truncated


def parse_verdict(text, rubric):
    start, end = text.find("{"), text.rfind("}")
    try:
        verdict = json.loads(text[start:end + 1]) if start >= 0 else None
    except ValueError:
        verdict = None
    criteria = verdict.get("criteria") if isinstance(verdict, dict) else None
    if not isinstance(criteria, list) or len(criteria) != len(rubric) or not all(
            isinstance(item, dict) and isinstance(item.get("passed"), bool) for item in criteria):
        raise JudgeError("judge reply is not a verdict with one boolean per criterion")
    return [{"criterion": expected, "passed": item["passed"], "reason": str(item.get("reason", ""))}
            for expected, item in zip(rubric, criteria)], str(verdict.get("summary", ""))


class AnthropicJudge:
    """Messages API over HTTPS; the key comes from the environment and is never stored."""

    url = "https://api.anthropic.com/v1/messages"

    def __init__(self, model, api_key, timeout=600, urlopen=urllib.request.urlopen, sleep=time.sleep, attempts=4):
        self.model, self.api_key, self.timeout, self.urlopen = model, api_key, timeout, urlopen
        self.sleep, self.attempts = sleep, attempts

    def __call__(self, prompt):
        body = json.dumps({"model": self.model, "max_tokens": 16000,
                           "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
        for attempt in range(self.attempts):
            request = urllib.request.Request(self.url, data=body, method="POST", headers={
                "content-type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"})
            try:
                with self.urlopen(request, timeout=self.timeout) as response:
                    reply = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as error:
                if error.code not in RETRY_STATUSES or attempt == self.attempts - 1:
                    raise JudgeError(f"judge request failed with HTTP {error.code}: {error.read()[:500]!r}")
            except (urllib.error.URLError, OSError, ValueError) as error:
                if attempt == self.attempts - 1:
                    raise JudgeError(f"judge request failed: {error}")
            self.sleep(2 ** (attempt + 1))
        if reply.get("stop_reason") == "refusal":
            raise JudgeError("judge declined the request")
        return "".join(block.get("text", "") for block in reply.get("content", []) if block.get("type") == "text")


class CommandJudge:
    """Any other judge: a command that reads the prompt on stdin and prints the verdict."""

    def __init__(self, command, timeout=600):
        self.command, self.timeout = command, timeout

    def __call__(self, prompt):
        try:
            run = subprocess.run(shlex.split(self.command), input=prompt, text=True,
                                 capture_output=True, timeout=self.timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise JudgeError(f"judge command failed: {error}")
        if run.returncode:
            raise JudgeError(f"judge command exited {run.returncode}: {run.stderr[-500:]}")
        return run.stdout


def judge_from_env(env=os.environ):
    """Build the judge from REEFSTACK_JUDGE_* settings; returns (judge, description, variables to hide)."""
    model = env.get("REEFSTACK_JUDGE_MODEL", "").strip()
    provider = env.get("REEFSTACK_JUDGE_PROVIDER", "anthropic").strip()
    if not model:
        raise SuiteError("set REEFSTACK_JUDGE_MODEL to a model from a different family than the agent")
    if provider == "anthropic":
        key = env.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise SuiteError("set ANTHROPIC_API_KEY for the judge, or REEFSTACK_JUDGE_PROVIDER=command")
        return AnthropicJudge(model, key), {"provider": provider, "model": model}, {"ANTHROPIC_API_KEY"}
    if provider == "command":
        command = env.get("REEFSTACK_JUDGE_COMMAND", "").strip()
        if not command:
            raise SuiteError("REEFSTACK_JUDGE_PROVIDER=command needs REEFSTACK_JUDGE_COMMAND")
        # The command judge's own credentials, named in REEFSTACK_JUDGE_SECRET_ENV, are hidden from the agent.
        hidden = {name.strip() for name in env.get("REEFSTACK_JUDGE_SECRET_ENV", "").split(",") if name.strip()}
        return CommandJudge(command), {"provider": provider, "model": model}, hidden
    raise SuiteError(f"unsupported REEFSTACK_JUDGE_PROVIDER '{provider}'; use anthropic or command")


def score(case, result, transcript, diff, judge, case_dir):
    """Judge one saved session and fill in criteria, score, and pass/fail."""
    prompt, truncated = judge_prompt(case, f"session-{result['run']}", transcript, diff, result["checks"])
    result.update(criteria=[], summary="", error=None, judge_input_truncated=truncated)
    try:
        reply = judge(prompt)
        (case_dir / "judge.txt").write_text(reply, encoding="utf-8")
        result["criteria"], result["summary"] = parse_verdict(reply, case["rubric"])
    except JudgeError as error:
        result["error"] = str(error)
    met = sum(item["passed"] for item in result["criteria"])
    result["score"] = round(met / len(case["rubric"]), 3)
    result["passed"] = (result["error"] is None and met == len(case["rubric"]) and result["agent_exit"] == 0
                        and not result["possible_unblinding"]
                        and all(check["passed"] for check in result["checks"].values()))
    return result


def run_case(case, run_number, agent, judge, out_dir, fixtures=EVALUATIONS / "fixtures", hidden=()):
    case_dir = Path(out_dir) / "cases" / case["id"] / f"run-{run_number}"
    case_dir.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as parent, tempfile.TemporaryDirectory() as scratch:
        project, base, head = prepare_workspace(case, fixtures, parent)
        env = agent_environment(case, scratch, project, hidden)
        transcript, status, seconds = run_agent(agent["command"], agent["model"], case["prompt"],
                                                project, env, agent["timeout"])
        checks = run_checks(case, project, base, head)
        diff = capture_diff(project, base)
    (case_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
    (case_dir / "diff.patch").write_text(diff, encoding="utf-8")
    probes = SUITE_FILES + (SANDBOX_PROBES if case.get("setup", {}).get("deny_port_binding") else ())
    result = {"case": case["id"], "run": run_number, "agent_exit": status, "agent_seconds": seconds,
              "checks": checks, "possible_unblinding": [name for name in probes if name in transcript]}
    return score(case, result, transcript, diff, judge, case_dir)


def plugin_state():
    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
    try:
        revision = git(ROOT, "rev-parse", "--short", "HEAD").strip()
        dirty = bool(git(ROOT, "status", "--porcelain", "--", "skills", "references", "harness", "hooks"))
    except SuiteError:
        revision, dirty = "unknown", None
    return {"version": manifest.get("version"), "revision": revision, "uncommitted_procedure_changes": dirty,
            "installation_in_agent": "not_checked"}


def summarize(results, cases, runs, full_suite, procedures_committed):
    per_case = {}
    for case in cases:
        own = [item for item in results if item["case"] == case["id"]]
        per_case[case["id"]] = {"passed_runs": sum(item["passed"] for item in own), "runs": len(own),
                                "mean_score": round(sum(item["score"] for item in own) / max(len(own), 1), 3)}
    every = all(entry["passed_runs"] == entry["runs"] == runs for entry in per_case.values())
    return {"cases": per_case, "all_passed": every,
            # Stopping rule: every case of the full suite passes on two or more consecutive runs of one
            # committed revision of the procedures.
            "stopping_rule_met": every and runs >= 2 and full_suite and procedures_committed}


def write_report(out_dir, report):
    (out_dir / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Reefstack evaluation {report['date']}", "",
             f"Agent: {report['agent']['model']} ({report['agent']['family']}). "
             f"Judge: {report['judge']['model']} ({report['judge']['family']}, {report['judge']['provider']}). "
             f"Reefstack {report['reefstack']['version']} at {report['reefstack']['revision']}.", "",
             f"Stopping rule met: {'yes' if report['summary']['stopping_rule_met'] else 'no'} "
             f"({report['runs']} run(s) per case).", "",
             "| Case | Run | Score | Passed | Checks | Judge summary |", "| --- | --- | --- | --- | --- | --- |"]
    for item in report["results"]:
        checks = ", ".join(f"{name} {'ok' if value['passed'] else 'FAIL'}" for name, value in item["checks"].items())
        leak = item["possible_unblinding"] and "possible unblinding: " + ", ".join(item["possible_unblinding"])
        note = (leak or item["error"] or item["summary"]).replace("|", "/").replace("\n", " ")
        lines.append(f"| {item['case']} | {item['run']} | {item['score']} | {'yes' if item['passed'] else 'no'} "
                     f"| {checks or '-'} | {note} |")
    for item in report["results"]:
        lines += ["", f"## {item['case']} run {item['run']}", ""]
        lines += [f"- {'pass' if c['passed'] else 'FAIL'}: {c['criterion']} {c['reason']}" for c in item["criteria"]]
        if item["error"]:
            lines.append(f"- error: {item['error']}")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_suite(cases, runs, agent, judge, judge_info, results_root, label, hidden=(),
              fixtures=EVALUATIONS / "fixtures", now=None, full_suite=True):
    now = now or datetime.now(timezone.utc)
    reefstack = plugin_state()  # recorded before the runs, so later edits cannot be credited
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "run"
    out_dir = Path(results_root) / f"{now:%Y-%m-%d}-{slug}"
    suffix = 2
    while out_dir.exists():
        out_dir = Path(results_root) / f"{now:%Y-%m-%d}-{slug}-{suffix}"
        suffix += 1
    out_dir.mkdir(parents=True)
    results = [run_case(case, number, agent, judge, out_dir, fixtures, hidden)
               for number in range(1, runs + 1) for case in cases]
    report = {"date": now.isoformat(timespec="seconds"), "label": label, "runs": runs, "full_suite": full_suite,
              "agent": {"model": agent["model"], "family": model_family(agent["model"]),
                        "command": agent["command"]},
              "judge": {**judge_info, "family": model_family(judge_info["model"])},
              "reefstack": reefstack, "results": results}
    report["summary"] = summarize(results, cases, runs, full_suite,
                                  reefstack["uncommitted_procedure_changes"] is False)
    write_report(out_dir, report)
    return out_dir, report


def rejudge(out_dir, judge, judge_info, cases, retry_all=False):
    """Score saved sessions again without rerunning the agent: failed judgments, or all with retry_all."""
    out_dir = Path(out_dir)
    report = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in cases}
    for result in report["results"]:
        if result["error"] is None and not retry_all:
            continue
        case = by_id[result["case"]]
        case_dir = out_dir / "cases" / result["case"] / f"run-{result['run']}"
        transcript = (case_dir / "transcript.txt").read_text(encoding="utf-8")
        diff = (case_dir / "diff.patch").read_text(encoding="utf-8")
        score(case, result, transcript, diff, judge, case_dir)
    report["judge"] = {**judge_info, "family": model_family(judge_info["model"])}
    selected = [by_id[name] for name in dict.fromkeys(result["case"] for result in report["results"])]
    report["summary"] = summarize(report["results"], selected, report["runs"], report.get("full_suite", False),
                                  report["reefstack"]["uncommitted_procedure_changes"] is False)
    write_report(out_dir, report)
    return report


def run_new(args, cases):
    """Run the selected cases as a new arm and return (results directory, report)."""
    full_suite = not args.case
    if args.case:
        unknown = set(args.case) - {case["id"] for case in cases}
        if unknown:
            raise SuiteError(f"unknown case ids: {sorted(unknown)}")
        cases = [case for case in cases if case["id"] in args.case]
    if args.runs < 1:
        raise SuiteError("--runs must be at least 1")
    if not args.agent_model:
        raise SuiteError("set --agent-model or REEFSTACK_AGENT_MODEL so results name the model")
    judge, judge_info, hidden = judge_from_env()
    agent_family, judge_family = model_family(args.agent_model), model_family(judge_info["model"])
    if agent_family == judge_family and agent_family != "unknown":
        raise SuiteError(f"judge and agent are both {agent_family} models; pick a judge from another family")
    if "unknown" in (agent_family, judge_family):
        print("warning: could not tell a model family apart; results record it as unknown", file=sys.stderr)
    agent = {"command": args.agent_command, "model": args.agent_model, "timeout": args.timeout}
    return run_suite(cases, args.runs, agent, judge, judge_info, args.results, args.label,
                     hidden=hidden, full_suite=full_suite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", help="run only this case id (repeatable)")
    parser.add_argument("--runs", type=int, default=1, help="consecutive runs per case (2+ for the stopping rule)")
    parser.add_argument("--label", default="reefstack", help="name for this arm, used in the results folder")
    parser.add_argument("--agent-model", default=os.environ.get("REEFSTACK_AGENT_MODEL"))
    parser.add_argument("--agent-command", default=os.environ.get("REEFSTACK_AGENT_COMMAND", DEFAULT_AGENT_COMMAND))
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per agent session")
    parser.add_argument("--results", default=str(EVALUATIONS / "results"))
    parser.add_argument("--list", action="store_true", help="list runnable cases and exit")
    parser.add_argument("--check", action="store_true", help="validate cases, fixtures, and blinding, then exit")
    parser.add_argument("--rejudge", metavar="RESULTS_DIR",
                        help="score saved sessions again (failed judgments only) without rerunning the agent")
    parser.add_argument("--all", action="store_true", help="with --rejudge, score every saved session again")
    args = parser.parse_args(argv)

    problems = validate_suite()
    if problems or args.check:
        print("\n".join(problems) or "evaluation suite ok")
        return 1 if problems else 0
    cases = load_cases()
    if args.list:
        for case in cases:
            print(f"{case['id']:<34} {case['fixture']:<8} {case['prompt']}")
        return 0
    try:
        if args.rejudge:
            judge, judge_info, _ = judge_from_env()
            saved = json.loads((Path(args.rejudge) / "results.json").read_text(encoding="utf-8"))
            if model_family(saved["agent"]["model"]) == model_family(judge_info["model"]) != "unknown":
                raise SuiteError("judge and agent are from the same family; pick a judge from another family")
            report, out_dir = rejudge(args.rejudge, judge, judge_info, cases, args.all), args.rejudge
        else:
            out_dir, report = run_new(args, cases)
    except (SuiteError, OSError, ValueError, KeyError) as error:
        print("run_evals: " + str(error), file=sys.stderr)
        return 2
    summary = report["summary"]
    print(f"{out_dir}\n{sum(e['passed_runs'] for e in summary['cases'].values())} of "
          f"{sum(e['runs'] for e in summary['cases'].values())} case runs passed; "
          f"stopping rule {'met' if summary['stopping_rule_met'] else 'not met'}")
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
