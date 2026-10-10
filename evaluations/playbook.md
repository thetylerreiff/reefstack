# Running the evaluation cases

`scripts/run_evals.py` runs the `runnable_cases` in `cases.json`. Each case runs a coding agent on a small sample app, saves what it did, and has a judge on a different model family score it against a rubric. The `activation_cases` remain written specifications; only `runnable_cases` run.

What a run shows: how one agent model, with whatever Reefstack setup its host has, behaved on these tasks, as judged by one other model. It does not prove native hook delivery, speed improvements, or behavior on other tasks. Do not publish benchmark claims without comparative runs.

## Before a run

1. Install and enable Reefstack in the agent's host and trust its hooks, the same way a user would. The runner never installs plugins or changes hook trust; its results record `installation_in_agent: not_checked`. For a comparison arm, run the same cases with the plugin disabled and a different `--label`.
2. Make sure the agent CLI works non-interactively. The default command is `codex exec --json --full-auto --skip-git-repo-check -m {model} -`, with the prompt on stdin and the project as the working directory. Override it with `--agent-command` or `REEFSTACK_AGENT_COMMAND`; `{model}` is replaced with the agent model.
3. Set the environment. Keys are read from the environment only; nothing is written to results.

| Variable | Purpose |
| --- | --- |
| `REEFSTACK_AGENT_MODEL` | Agent model, recorded in results (or `--agent-model`). Required. |
| `REEFSTACK_AGENT_COMMAND` | Optional agent command template. |
| `REEFSTACK_JUDGE_MODEL` | Judge model. Required; must be a different family from the agent, or the run stops. |
| `REEFSTACK_JUDGE_PROVIDER` | `anthropic` (default, Messages API) or `command`. |
| `ANTHROPIC_API_KEY` | Key for the `anthropic` provider. Removed from the agent's environment. |
| `REEFSTACK_JUDGE_COMMAND` | For `command`: a program that reads the judge prompt on stdin and prints the reply. Use it for any other provider. |

## Commands

```sh
python3 scripts/run_evals.py --check                 # cases, fixtures, and blinding; no model calls
python3 scripts/run_evals.py --list
python3 scripts/run_evals.py --case web-typo-no-launch
python3 scripts/run_evals.py --runs 2 --label reefstack    # full suite, stopping-rule run
python3 scripts/run_evals.py --runs 2 --label baseline     # same cases, plugin disabled
```

Each case run costs one agent session (up to `--timeout`, default 1800 seconds) and one judge call. Exit status is 0 only when every case run passed.

## Blinding

Agents behave differently when they can tell they are being measured, so nothing the agent sees says so:

- The fixture is copied into a project named after the app (`pantry`, `tally`) in a random temporary directory, committed as `Initial commit` by an ordinary author. Setup patches become ordinary commits with ordinary messages.
- The prompt is what a user would type. The rubric, the case id, and the checks never reach the agent.
- `REEFSTACK_*` variables and the judge's key are removed from the agent's environment.
- `--check`, which `scripts/health.py` also runs, rejects words such as eval, judge, rubric, score, benchmark, candidate, or experiment in prompts, project names, fixture paths and files, and patches. "test" is allowed: real apps have checks and real users ask to test their app.
- The judge sees the session as `session-N`, never the agent's model name.

Reefstack's own skills use words like "review rubric". That is part of the setup being measured, not a signal about the run. The installed plugin also contains `evaluations/`, so an agent that browses the plugin's own files could find these cases; a case run whose transcript mentions `cases.json`, `playbook.md`, or `run_evals.py` is marked `possible_unblinding` and fails. Read it and rerun.

The `web-launch-blocked` case simulates a sandbox that refuses local ports: a `sitecustomize.py` outside the project makes socket binding fail for Python processes in the agent's environment. A non-Python server would not be blocked, so the case uses the Python fixture.

## Reading results

Each run writes `evaluations/results/<date>-<label>/`:

- `results.json`: date, agent model and family, judge provider, model and family, Reefstack version and revision, and per case run the score, pass/fail, deterministic check results, each criterion's verdict and reason, and any error.
- `summary.md`: the same as a table, plus each criterion's reason.
- `cases/<case>/run-<n>/`: `transcript.txt`, `diff.patch`, and the judge's raw `judge.txt`. These stay local (gitignored and excluded from release archives); commit `results.json` and `summary.md` if you want a history.

How to read them:

- **Score** is the fraction of rubric criteria the judge passed. **Passed** needs every criterion, every deterministic check (`map_lint`, `map_current`, `no_edits`), and no possible unblinding. A judge error or unparseable reply is a failure, never a pass.
- Deterministic checks outrank the judge. When they disagree, read the transcript.
- Read a sample of transcripts and diffs yourself, including every failure. Repeated disagreement with the judge means a biased judge or an ambiguous criterion: fix the criterion and say so in the commit, rather than accepting either side silently.
- Compare arms only with the same agent model, cases, and settings.

## Stopping rule

Keep changing a skill until **every case passes on two consecutive runs** of the same Reefstack revision: `--runs 2` with `stopping_rule_met: yes` in the summary. Any edit to `skills/`, `references/`, `harness/`, or `hooks/` resets the streak; run the full suite again, not only the case that failed. Results record uncommitted procedure changes so a streak cannot silently span two versions.

When a case fails, fix the procedure, not the case. Change a rubric or prompt only when it is wrong, never to turn a failure into a pass, and record why. Never delete a case to meet the rule. A failure seen twice goes in `docs/failure-log.md` and is considered for a check, per [enforcement](../references/enforcement.md).

## Adding a case

Add an entry to `runnable_cases` with an `id`, a `fixture` under `fixtures/`, an organic `prompt`, three to six concrete `rubric` criteria the judge can decide from a transcript and diff, optional `checks`, and optional `setup` (`patches` with commit messages, `remove`, `deny_port_binding`). Run `--check`, and add a test when the case needs new runner behavior.
