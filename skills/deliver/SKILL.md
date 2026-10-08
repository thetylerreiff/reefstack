---
name: deliver
description: Implement and continuously integrate authorized substantial engineering changes, delegating independent pieces to explorers and workers to shorten verified delivery and protect the main context.
---

# Deliver

Keep the main agent on uncertainty, contracts, the critical path, and integration. Delegate everything else that a trigger below covers; do the rest directly.

Before fan-out, confirm that shared contracts are established and blocking probes passed. Name the independent workstreams, exclusive ownership, shared state, acceptance checks, and smallest useful decomposition. Write each brief from [the delegation briefs](../../references/worker-brief.md).

## Delegate when

- **Explorer:** you need facts spread across many files, an unknown location, or a long read whose conclusion is all you need. Several independent questions go to several explorers at once.
- **Worker:** a substantial piece has its own writable files and an agreed contract. Two or more such pieces run in parallel.
- **Mechanical worker:** repetitive bounded edits with a clear selection rule and a check that proves coverage. Prefer an existing codemod or script when one can do it reliably.
- **Reviewer:** the integrated change is substantial; see [review](../review/SKILL.md).

## Keep it direct when

The change is small or tightly coupled, file ownership cannot be separated, the contract is still unproven, or the work is the critical-path piece you would wait on anyway. Hard cross-cutting, concurrency, or algorithmic work stays with the main agent or goes to an explicitly chosen stronger worker.

## Run it

Select each helper's configured role model and effort explicitly. Launch independent helpers in the same turn, then continue main-agent work instead of waiting idle. Do not repeat work you delegated, and do not poll; inspect results as each one arrives rather than waiting for a whole batch. Respect the runtime's actual concurrency cap.

Use explorer findings as reliable leads and check the specific fact a consequential decision rests on. Review worker diffs against their acceptance checks, preserve others' changes, and integrate with boundary checks. The parent owns every accepted result.

Separate transient infrastructure failures from correctness failures. A bounded infrastructure retry may be appropriate. After two corrections fail the same acceptance condition, the main agent reproduces and investigates the shared premise before another worker attempt. A contract failure blocks dependent pieces, not unrelated progress.

Use [verify](../verify/SKILL.md) for the integrated path and [review](../review/SKILL.md) for substantial changes. Fix accepted findings and recheck affected behavior. Report changed behavior, actual verification, and residual gaps, without treating worker summaries as proof.
