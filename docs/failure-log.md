# Failure log

Observed failures in Reefstack's own development and what each became. See [enforcement](../skills/reefstack/references/enforcement.md) for when a failure turns into a check. `tests/test_failure_log.py` keeps entries in this shape.

### Root plugin.json suppressed Codex hooks

- Seen: 2026-10-08, host check with `hooks/list` (Codex 0.162.0-alpha.2)
- Cause: a root Agent Plugins `plugin.json` made Codex discover no plugin hooks, so no context reached a session.
- Became: check
- Enforced by: no longer applicable since 0.4.0 removed the hooks; `scripts/health.py` refuses hooks in the package or manifest

### Map lint rejected real todo-app handles

- Seen: 2026-10-10, independent review of the feature-map change
- Cause: the placeholder pattern matched any text starting with "todo", so `todo add` commands failed the lint.
- Became: check
- Enforced by: `tests/test_map_lint.py` test_todo_app_handles_are_not_placeholders

### "not verified" satisfied the Last checked status

- Seen: 2026-10-10, independent review of the feature-map change
- Cause: the lint searched for a status word anywhere, so a negated status passed.
- Became: check
- Enforced by: `skills/map/scripts/map_lint.py` requires a `Status:` line; `tests/test_map_lint.py` test_last_checked_needs_a_status_and_must_come_last

### Stopping rule credited a partial suite

- Seen: 2026-10-10, independent review of the evaluation runner
- Cause: `--case X --runs 2` reported the stopping rule met, and uncommitted procedure edits did not reset it.
- Became: check
- Enforced by: `tests/test_run_evals.py` test_stopping_rule_needs_every_case_on_consecutive_runs

### Agent-started servers outlived the session

- Seen: 2026-10-10, independent review of the evaluation runner
- Cause: a background server from one run kept its port and the runner's output pipe into the next run.
- Became: check
- Enforced by: `scripts/run_evals.py` stops the agent's process group; `tests/test_run_evals.py` test_agent_exit_failure_and_leftover_servers

### Live workflow trials skipped map validation

- Seen: 2026-10-10, import probe omitted `## What it is`; resume probe wrote `cli alias:` instead of `cli:`
- Cause: agents edited maps without running the existing linter; the completion guidance focused on moved entry points and hid the command in an unread procedure.
- Became: check
- Enforced by: `tests/test_run_evals.py` test_live_trial_map_mistakes_fail_until_repaired; `skills/verify/SKILL.md` links the linter; `skills/reefstack/references/verification.md` defines the completion check

### Shape-valid map omitted a new command

- Seen: 2026-10-10, fresh import workflow trial after exposing the map linter
- Cause: the agent kept the old map unchanged; shape validation cannot detect a missing new feature and the maintenance guidance emphasized moves.
- Became: check
- Enforced by: `scripts/run_evals.py` import_map_entry; `tests/test_run_evals.py` test_import_case_requires_new_command_coverage_not_just_valid_shape

### Ephemeral CLI trials persisted temporary-project trust

- Seen: 2026-10-10, native-hook configuration guard during concurrent behavior probes
- Cause: raw `codex exec --ephemeral --ignore-user-config` still saved trust for each generated project.
- Became: check
- Enforced by: `scripts/run_evals.py` supplies invocation-only project trust by default; `tests/test_run_evals.py` checks exact argument transport
