---
name: deliver
description: Implement and continuously integrate authorized substantial engineering changes, delegating independent pieces to helpers when that shortens verified delivery or protects the main context.
---

# Deliver

Use these coordination methods at the implementation step of the selected playbook; that playbook owns workflow order and completion. Keep the main agent on uncertainty, contracts, the critical path, and integration. Delegate when a trigger below covers useful independent work; do the rest directly. A routine procedure does not itself require helpers.

Before fan-out, confirm that shared contracts are established and blocking probes passed. Name the independent workstreams, exclusive ownership, shared state, acceptance checks, and smallest useful decomposition. Write each brief from [the delegation briefs](../reefstack/references/worker-brief.md). Workers return evidence and blockers; a returned result is not yet integrated or verified. When a contract changes, mark affected dependent work and evidence stale before continuing it.

## Delegate when

- **Long or scattered reads:** you need facts spread across many files, an unknown location, or a long read whose conclusion is all you need. Send each independent question to its own read-only helper at once.
- **Independent writable pieces:** a substantial piece has its own files and an agreed contract. Two or more such pieces run in parallel.
- **Repetitive edits:** many bounded edits follow a clear selection rule and a check proves coverage. Prefer an existing codemod or script when one can do it reliably.
- **Work that would block the critical path:** cross-cutting, environment, test-infrastructure, or debugging work the main agent would otherwise wait on.
- **Review:** the integrated change needs a fresh reviewer after every worker has handed back; see [review](../review/SKILL.md).

## Keep it direct when

The change is small or tightly coupled, file ownership cannot be separated, the contract is still unproven, or the work is the critical-path piece you would wait on anyway. Shared state that only one agent should touch (a running app being driven, a database being seeded) stays with one owner. Local environment work (temporary databases, seeding, starting servers) stays direct unless the user asks.

## Run it

Choose each helper's model and effort for its work. Launch independent helpers in the same turn, then continue main-agent work instead of waiting idle. Do not repeat work you delegated or read inside a running helper's scope, and do not poll; inspect results as each one arrives rather than waiting for a whole batch. Respect the runtime's actual concurrency cap.

Use read-only findings as reliable leads and check the specific fact a consequential decision rests on. Review worker diffs against their acceptance checks, preserve others' changes, and integrate with boundary checks. The parent owns every accepted result.

Separate transient infrastructure failures from correctness failures. A bounded infrastructure retry may be appropriate. After two corrections fail the same acceptance condition, the main agent reproduces and investigates the shared premise before another worker attempt. A contract failure blocks dependent pieces, not unrelated progress.

Return integrated work and evidence to the selected playbook's next step. Worker summaries alone are not proof. PR work uses [PR follow-up](../reefstack/references/playbooks/pr-follow-up.md); coordination does not grant publication or merge authority.

Before spawning a helper, read the host's [delegation mechanics](../reefstack/harness/delegation.md) and brief it with the [worker brief](../reefstack/references/worker-brief.md).
