# Verification

This report distinguishes checks of the package from native host activation. Updated October 8, 2026.

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

The icon is a square 1254-by-1254 PNG, below the documented size limit, referenced by both logo and composerIcon.

CI runs the package health check and tests and checks an extracted standalone archive. The workflow status shows its actual result; the existence of the workflow is not a passing run.

## Behavioral evidence and limits

Isolated forward-tests with supplied startup context exercised a direct visual edit, a read-only contract discussion, and a bounded parser/rendering/CLI feature. These tested guidance under supplied context, not native lifecycle delivery. They were not blinded comparisons against other workflows.

Native desktop startup/resume/compaction delivery, trust state, substantial-task automatic delegation and review, and end-to-end speed improvements remain environment-specific acceptance checks. Skill discovery alone does not prove any of those states.

## Acceptance in a host

Install and enable Reefstack through the supported interface, review and trust its hook definition, and start a fresh engineering chat. Exercise evaluations/cases.json and inspect actual actions, artifacts, and reviewer activity.

Include a substantial multi-component task, a small local edit, a planning-only request, a failed-worker correction, and unavailable-model handling. Check resume, compaction, and disablement in a fresh session. Record the client version, actual models, code state, checks, elapsed time, corrective rounds, and any escaped defects.

A skipped runtime check is not a pass. Package validity, installation, enablement, trust, context delivery, and verified behavior are separate results.
