# Running the evaluation cases

`scripts/run_evals.py` runs the `runnable_cases` in `cases.json`. Each case runs a coding agent on a small sample app, saves what it did, and has a judge on a different model family score it against a rubric. The `activation_cases` remain written specifications; only `runnable_cases` run.

What a run shows: how one agent model, with whatever Reefstack setup its host has, behaved on these tasks, as judged by one other model. It does not prove native hook delivery, speed improvements, or behavior on other tasks. Do not publish benchmark claims without comparative runs.

## Workflow coverage

The small typo case requires a direct edit without creating a task record. `workflow-substantial-record` asks for a CSV import command with validation and persistence constraints; its rubric checks for a useful, current record alongside implementation and integration evidence.

`workflow-resume-new-constraint` and `workflow-read-only-pickup` start new agent sessions with a supplied record under `.reefstack/tasks/`. A setup patch applies a partial command rename and the record as an ordinary project commit. The record describes returned worker changes and older verification from another checkout; the current project still lacks those test and documentation changes. The resume request adds a newer requirement to preserve the old command as an alias. The read-only request asks for an assessment and next step without edits, including record edits.

These are supplied-record continuation scenarios. They check whether the agent reconciles the handoff with current instructions, Git state, source, evidence and user intent. They do not simulate native compaction, retain an earlier conversation, launch real workers for the handoff, or prove multi-turn continuity. Preparing the patch and running deterministic checks proves the setup and checks work; behavioral acceptance still needs recorded agent sessions and judgments.

The separate [native lifecycle probe](../harness/lifecycle.md) runs an actual staged conversation through compaction and an app-server process restart. It supplies current repository guidance and excludes installed plugins per turn to avoid testing an older cached release. It is an acceptance probe with explicit staged prompts, not part of this blinded suite or proof of native hook delivery.

The fixture records are stored inside patches because release packaging excludes literal dot directories. Packaging tests extract the release, prepare the patched Git project, and exercise its checks so that this coverage works from an archive too.

## Refactor, performance and prototype coverage

Three cases use `dispatch`, a standard-library CLI that joins shipment orders to
an address book and writes a CSV manifest. Its ordinary project tests cover a few
common behaviors; the fuller acceptance checks stay outside the agent's project
in `tests/test_playbook_behavior.py`.

- `playbook-refactor-preserves-behavior` requests a real separation of argument
  handling, manifest construction and file I/O. Acceptance requires observed
  behavior before edits and equivalence after them, including CSV bytes, errors,
  exit statuses, first-match duplicate customers, weight boundaries and failure
  without partial output. Code organization alone cannot pass it.
- `playbook-performance-measured` requests faster manifests on the supplied
  deterministic 18000-order/3000-customer workload and smaller inputs. The
  starting implementation searches the address book for each order. Acceptance
  requires measured diagnosis, repeated real-command timings under matched
  conditions, meaningful improvement and preserved correctness. Timing data
  generation or only an isolated helper cannot pass it. There is no fixed timing
  assertion in unit tests because machine load varies.
- `playbook-prototype-disposable` requests two working local pickup-selection
  sketches and a recommendation supported by actual interactions. All files
  belong under `scratch/pickup`; production source, tests and docs must stay
  unchanged. Acceptance includes select/remove, empty selection and a search
  with no match, plus observed count and weight changes. Screenshots of an inert
  design or a production implementation cannot pass it.

These cases select different procedures without imposing a task record merely
because a playbook exists. The small no-record and supplied-record continuation
cases above remain separate checks of proportional effort and resumed work.

Run one live session per case with the regular agent/judge configuration:

```sh
python3 scripts/run_evals.py --case playbook-refactor-preserves-behavior
python3 scripts/run_evals.py --case playbook-performance-measured
python3 scripts/run_evals.py --case playbook-prototype-disposable
```

Validate the original fixture contracts without a model call:

```sh
python3 -m unittest discover -s tests -p test_playbook_behavior.py -v
python3 -m unittest discover -s tests -p test_run_evals.py -v
python3 scripts/run_evals.py --check
```

For a separately retained trial checkout, run the same held-out CLI contract
checks with `DISPATCH_PROJECT=/absolute/path/to/dispatch` prefixed to the first
command. The normal runner deletes its temporary checkout, so these are not an
automatic post-run gate. They verify CLI behavior, input preservation and
deterministic data generation; they do not establish that an agent captured a
baseline, measured an improvement, drove either prototype, or followed the right
procedure. Those require saved live-session evidence and rubric judgment. For a
prototype trial, also compare the final production files with its starting Git
revision; any changed file outside `scratch/pickup` violates its scope.

## Before a run

1. Install and enable Reefstack in the agent's host and trust its hooks, the same way a user would. The runner never installs plugins or changes hook trust; its results record `installation_in_agent: not_checked`. For a comparison arm, run the same cases with the plugin disabled and a different `--label`.
2. Make sure the agent CLI works non-interactively. The default command is `codex exec --json --ephemeral --approve-for-me --skip-git-repo-check -c {project_trust} -m {model} -`, with the prompt on stdin and the project as the working directory. This uses the current CLI's workspace sandbox and automatic approval review without persisting a chat. Native trials found that `--ephemeral` and `--ignore-user-config` do not prevent this CLI from saving trust for a temporary project; they are not a configuration-isolation guarantee. The default therefore supplies `{project_trust}` as an invocation-only `projects` table for the generated fixture. Custom commands must preserve equivalent isolation or inspect such side effects. Override it with `--agent-command` or `REEFSTACK_AGENT_COMMAND` for another CLI version; `{model}` is replaced with the agent model and `{project_trust}` with that fixture’s scoped configuration, after argument splitting; neither value is evaluated by a shell. Each session runs in its own process group, which is stopped when the agent exits or times out, so servers it started do not carry into the next case.
3. Run from a repository checkout. A release archive works too: fixture ignore files ship as `gitignore` and become `.gitignore` in the workspace.
4. Set the environment. Keys are read from the environment only; nothing is written to results.

| Variable | Purpose |
| --- | --- |
| `REEFSTACK_AGENT_MODEL` | Agent model, recorded in results (or `--agent-model`). Required. |
| `REEFSTACK_AGENT_COMMAND` | Optional agent command template. |
| `REEFSTACK_JUDGE_MODEL` | Judge model. Required; must be a different family from the agent, or the run stops. |
| `REEFSTACK_JUDGE_PROVIDER` | `anthropic` (default, Messages API) or `command`. |
| `ANTHROPIC_API_KEY` | Key for the `anthropic` provider. Removed from the agent's environment. |
| `REEFSTACK_JUDGE_COMMAND` | For `command`: a program that reads the judge prompt on stdin and prints the reply. Use it for any other provider. |
| `REEFSTACK_JUDGE_SECRET_ENV` | For `command`: comma-separated names of the judge's credential variables, removed from the agent's environment. |

## Commands

```sh
python3 scripts/run_evals.py --check                 # cases, fixtures, and blinding; no model calls
python3 scripts/run_evals.py --list
python3 scripts/run_evals.py --case web-typo-no-launch
python3 scripts/run_evals.py --runs 2 --label reefstack    # full suite, stopping-rule run
python3 scripts/run_evals.py --runs 2 --label baseline     # same cases, plugin disabled
python3 scripts/run_evals.py --rejudge evaluations/results/2026-10-10-reefstack   # retry failed judgments
python3 scripts/run_evals.py --rejudge evaluations/results/2026-10-10-reefstack --all
```

Each case run costs one agent session (up to `--timeout`, default 1800 seconds) and one judge call. The judge retries rate-limit and overload responses; a judgment that still fails can be retried with `--rejudge` from the saved transcript and diff, without another agent session. Exit status is 0 only when every case run passed.

## Blinding

Agents behave differently when they can tell they are being measured, so nothing the agent sees says so:

- The fixture is copied into a project named after the app (`pantry`, `tally`, `dispatch`) in a random temporary directory, committed as `Initial commit` by an ordinary author. Setup patches become ordinary commits with ordinary messages.
- The prompt is what a user would type. The rubric, the case id, and the checks never reach the agent.
- `REEFSTACK_*` variables and the judge's key are removed from the agent's environment, `PWD` is the project, and `OLDPWD` is unset.
- `--check`, which `scripts/health.py` also runs, rejects words such as eval, judge, rubric, score, benchmark, candidate, or experiment in prompts, project names, fixture paths and files, and patches. "test" is allowed: real apps have checks and real users ask to test their app.
- The judge sees the session as `session-N`, never the agent's model name.

Reefstack's own skills use words like "review rubric". That is part of the setup being measured, not a signal about the run. The installed plugin also contains `evaluations/`, so an agent that browses the plugin's own files could find these cases; a case run whose transcript mentions `cases.json`, `playbook.md`, or `run_evals.py` is marked `possible_unblinding` and fails. Read it and rerun.

The `web-launch-blocked` case simulates a sandbox that refuses local ports: a module on `PYTHONPATH`, outside the project, makes socket binding fail for Python processes with `PermissionError: [Errno 1] Operation not permitted`, and the traceback shows `<frozen socket>` rather than the injected file. It is a simulation, not an OS sandbox: a non-Python server would not be blocked, and an agent that clears `PYTHONPATH` gets past it. A transcript in that case that mentions `PYTHONPATH` or `sitecustomize` is marked `possible_unblinding` and fails.

## Reading results

Each run writes `evaluations/results/<date>-<label>/`:

- `results.json`: date, agent model and family, judge provider, model and family, Reefstack version and revision, and per case run the score, pass/fail, deterministic check results, each criterion's verdict and reason, and any error.
- `summary.md`: the same as a table, plus each criterion's reason.
- `cases/<case>/run-<n>/`: `transcript.txt`, `diff.patch`, and the judge's raw `judge.txt`. These stay local (gitignored and excluded from release archives); commit `results.json` and `summary.md` if you want a history.

How to read them:

- **Score** is the fraction of rubric criteria the judge passed. **Passed** needs every criterion, every requested deterministic check (`map_lint`, `map_current`, `import_map_entry`, `no_edits`, `no_task_record`, `task_record`, `task_handoff`), an agent exit status of 0, and no possible unblinding. A judge error, an unparseable reply, a timeout, or a crashed agent is a failure, never a pass.
- `import_map_entry` is specific to the import fixture: it requires a typed CLI entry for `tally import` under a feature's `How to reach it` section. Shape lint alone cannot detect a new command missing from an otherwise valid map.
- `task_record` requires a nonempty Markdown record under `.reefstack/tasks/` for the substantial fixture. Its semantic accuracy, evidence, and current state are assessed by the rubric, not the file-existence check. Before workspace cleanup, `task-state.json` and `task-state/` preserve final records and supporting files independently of Git ignore rules. Judging and rejudging use that same snapshot. It is limited to 2 MB and 256 entries, never follows symlinks, and lists omissions; binary files are preserved for inspection but are not rendered to the text judge. References outside the task directory still need evidence in the transcript or diff.
- `task_handoff` requires a successful `task_handoff.py` readback matching the final record bytes and the returned link in the last assistant message. It catches both omitted readback/link and a readback made stale by later edits. This check currently parses Codex `--json` events; unsupported transcript formats fail closed and need an adapter. It proves observed transport and file identity, not the truth of the record.
- `no_task_record` fails when any file or symlink is present under `.reefstack/tasks/`, including ignored or committed files. It guards the default record location for the small task; its rubric also checks for unnecessary planning and delegation. `no_edits` rejects tracked or untracked working-tree changes and new commits, so a read-only handoff cannot be satisfied by updating the supplied record. Git-ignored runtime files such as Python bytecode do not count as edits.
- `judge_input_truncated` lists inputs cut in the middle to fit the judge (over 300,000 characters of transcript or 200,000 of diff). A criterion about omitted output may then be unjudgeable; read the saved files.
- Deterministic checks outrank the judge. When they disagree, read the transcript.
- Read a sample of transcripts and diffs yourself, including every failure. Repeated disagreement with the judge means a biased judge or an ambiguous criterion: fix the criterion and say so in the commit, rather than accepting either side silently.
- Compare arms only with the same agent model, cases, and settings.

## Stopping rule

Keep changing a skill until **every case passes on two consecutive runs** of the same Reefstack revision: the full suite with `--runs 2` and `stopping_rule_met: yes` in the summary. A `--case` subset or a checkout with uncommitted changes under `skills/`, `references/`, `harness/`, or `hooks/` never meets the rule; the revision is recorded before the runs start. Any procedure edit resets the streak: run the full suite again, not only the case that failed. The agent host must load that same revision; the runner cannot check this, so confirm the installed plugin version.

When a case fails, fix the procedure, not the case. Change a rubric or prompt only when it is wrong, never to turn a failure into a pass, and record why. Never delete a case to meet the rule. A failure seen twice goes in `docs/failure-log.md` and is considered for a check, per [enforcement](../references/enforcement.md).

## Adding a case

Add an entry to `runnable_cases` with an `id`, a `fixture` under `fixtures/`, an organic `prompt`, three to six concrete `rubric` criteria the judge can decide from a transcript and diff, optional `checks`, and optional `setup` (`patches` with commit messages, `remove`, `deny_port_binding`). Run `--check`, and add a test when the case needs new runner behavior.
