# Failure log

Observed failures in Reefstack's own development and what each became. See [enforcement](../references/enforcement.md) for when a failure turns into a check. `tests/test_failure_log.py` keeps entries in this shape.

### Root plugin.json suppressed Codex hooks

- Seen: 2026-10-08, host check with `hooks/list` (Codex 0.162.0-alpha.2)
- Cause: a root Agent Plugins `plugin.json` made Codex discover no plugin hooks, so no context reached a session.
- Became: check
- Enforced by: `scripts/health.py` refuses a root `plugin.json`; `tests/test_context.py` asserts the manifest location

### Map lint rejected real todo-app handles

- Seen: 2026-10-10, independent review of the feature-map change
- Cause: the placeholder pattern matched any text starting with "todo", so `todo add` commands failed the lint.
- Became: check
- Enforced by: `tests/test_map_lint.py` test_todo_app_handles_are_not_placeholders

### "not verified" satisfied the Last checked status

- Seen: 2026-10-10, independent review of the feature-map change
- Cause: the lint searched for a status word anywhere, so a negated status passed.
- Became: check
- Enforced by: `scripts/map_lint.py` requires a `Status:` line; `tests/test_map_lint.py` covers negations

### Moved entry point left the map stale

- Seen: 2026-10-10, raised as a known risk when adding the feature map; not yet observed in an agent run
- Cause: nothing failed when a change renamed a route or command and the map still named the old one; it relied on the agent remembering.
- Became: check
- Enforced by: `scripts/map_lint.py --since <base>`; rename tests in `tests/test_map_lint.py`
