# Verification

This report distinguishes checks of the package from native host activation. Updated October 10, 2026.

## Package and runtime checks

The local health check and unittest suite exercise:

- Manifest and skill references, lifecycle matchers, and declared shell commands.
- Startup, resume, clear, compaction, and delegated-agent context.
- Partial model overrides and disabled output.
- Input/settings rejection and exclusion of untrusted payload text from generated context.
- Relocation and shell quoting when the package path contains spaces.
- Separation of coordinator and delegated-agent context.
- Role configuration and separation of core procedures from named host/model mechanics.
- Standalone archive layout, inclusion, exclusions, output safety, and extraction.
- Feature-map lint: required sections and order, typed non-empty entry points, index coverage, `Last checked` statuses, CLI exit codes, and health's lint of the packaged template and any `docs/verification/`.
- Map drift check (`--since`): a renamed route in the web fixture and a renamed subcommand in the CLI fixture are flagged in real git repositories, and clear once the map moves or the old name is kept as an alias.
- Evaluation runner: case and fixture validation, blinding rejection, neutral workspaces, environment scrubbing, simulated port-binding denial, cleanup of servers the agent leaves running, deterministic checks and agent exit status overriding the judge, judge-reply failures and retries, input truncation, re-judging saved sessions, the stopping rule (full suite, committed procedures, consecutive runs), the judge's request shape, key handling, and the command-line transport, all with a fake agent and a mock judge. No model was called.
- Failure log entries name an outcome and an enforcing file that exists.

The icon is a square 1254-by-1254 PNG, below the documented size limit, referenced by both logo and composerIcon.

CI runs the package health check and tests and checks an extracted standalone archive. The workflow status shows its actual result; the existence of the workflow is not a passing run.

## Behavioral evidence and limits

Isolated forward-tests with supplied startup context exercised a direct visual edit, a read-only contract discussion, and a bounded parser/rendering/CLI feature. These tested guidance under supplied context, not native lifecycle delivery. They were not blinded comparisons against other workflows.

The grill scenarios in `evaluations/cases.json` specify intended positive and negative routing behavior, including vague product intent, an explicit request to pressure-test, clear substantial requirements, a tiny edit, and technical uncertainty that should be researched. They are evaluation cases, not completed test results. Those case definitions do not establish grill behavior or native automatic activation. Two isolated first-turn checks with supplied startup context observed a focused bottleneck question for an ambiguous merge-bot idea with no edits, and a direct header-color edit with no interview. They do not establish adaptive follow-up behavior or native lifecycle delivery.

No runnable case has been run against a real agent and judge yet; there are no results in `evaluations/results/`. The app-driving cases in `evaluations/cases.json` (a UI change that must be driven, a typo that must not launch the app, a sandbox-blocked launch that must be reported as blocked, a moved entry point that must update the map, and an explicit map request) are specifications, not completed runs. The lint checks a map's shape, not whether its entry points still match the app; that depends on agents following the verify procedure and on review.

Codex's `hooks/list` (0.162.0-alpha.2) returns no Reefstack hooks while a root Agent Plugins `plugin.json` exists, even with `extensions.com.openai.hooks`. With only `.codex-plugin/plugin.json`, it lists the SessionStart and SubagentStart hooks as untrusted, ready for review.

Native desktop startup/resume/compaction delivery, trust state, substantial-task automatic delegation and review, and end-to-end speed improvements remain environment-specific acceptance checks. Skill discovery alone does not prove any of those states.

## Acceptance in a host

Install and enable Reefstack through the supported interface, review and trust its hook definition, and start a fresh engineering chat. Exercise evaluations/cases.json, including both the grill and skip cases, and inspect actual questions, research, actions, artifacts, and reviewer activity.

Include a substantial multi-component task, a small local edit, a planning-only request, a failed-worker correction, and unavailable-model handling. Check resume, compaction, and disablement in a fresh session. Record the client version, actual models, code state, checks, elapsed time, corrective rounds, and any escaped defects.

A skipped runtime check is not a pass. Package validity, installation, enablement, trust, context delivery, and verified behavior are separate results.
