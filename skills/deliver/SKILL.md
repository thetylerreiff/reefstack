---
name: deliver
description: Implement and continuously integrate authorized substantial engineering changes, delegating independent pieces to explorers and workers to shorten verified delivery and protect the main context.
---

# Deliver

Use these coordination methods at the implementation step of the selected playbook; that playbook owns workflow order and completion. Keep the main agent on uncertainty, contracts, the critical path, and integration. Delegate when a trigger below covers useful independent work; do the rest directly. A routine procedure does not itself require helpers.

Before fan-out, confirm that shared contracts are established and blocking probes passed. Name the independent workstreams, exclusive ownership, shared state, acceptance checks, and smallest useful decomposition. Write each brief from [the delegation briefs](../../references/worker-brief.md).

For substantial work, put ownership, dependencies, and the contract revision in the existing [task record](../../references/task-record.md). The coordinator owns its updates; workers return evidence and blockers. A returned result is not yet integrated or verified. When a contract changes, mark affected dependent work and receipts stale before continuing it.

## Delegate when

- **Explorer:** you need facts spread across many files, an unknown location, or a long read whose conclusion is all you need. Several independent questions go to several explorers at once.
- **Worker:** a substantial piece has its own writable files and an agreed contract. Two or more such pieces run in parallel.
- **Mechanical (`mechanical` role):** repetitive bounded edits with a clear selection rule and a check that proves coverage. Prefer an existing codemod or script when one can do it reliably.
- **Heavy worker (`heavy_worker` role):** cross-cutting, concurrency, algorithmic, environment, test-infrastructure, or debugging work that would otherwise wait on the main agent.
- **Reviewer:** the integrated change is substantial and every worker has handed back; see [review](../review/SKILL.md).

## Keep it direct when

The change is small or tightly coupled, file ownership cannot be separated, the contract is still unproven, or the work is the critical-path piece you would wait on anyway. Local environment work (temporary databases, seeding, starting servers) stays direct with no explorer or reviewer unless the user asks.

## Run it

Select each helper's configured role model and effort explicitly. Launch independent helpers in the same turn, then continue main-agent work instead of waiting idle. Do not repeat work you delegated or read inside a running explorer's scope, and do not poll; inspect results as each one arrives rather than waiting for a whole batch. Respect the runtime's actual concurrency cap.

Use explorer findings as reliable leads and check the specific fact a consequential decision rests on. Review worker diffs against their acceptance checks, preserve others' changes, and integrate with boundary checks. The parent owns every accepted result.

Separate transient infrastructure failures from correctness failures. A bounded infrastructure retry may be appropriate. After two corrections fail the same acceptance condition, the main agent reproduces and investigates the shared premise before another worker attempt. A contract failure blocks dependent pieces, not unrelated progress.

Return integrated work and evidence to the selected playbook's next step. Worker summaries alone are not proof. PR work uses [PR follow-up](../../references/playbooks/pr-follow-up.md); coordination does not grant publication or merge authority.
