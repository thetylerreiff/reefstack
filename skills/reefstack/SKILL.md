---
name: reefstack
description: Coordinate substantial or consequential engineering work from ordinary conversation through preparation, implementation, integration, verification, and independent review.
---

# Reefstack

Optimize time to verified completion while preserving correctness and maintainability. Keep the parent model and effort the user selected. Supporting procedures are available without requiring the user to invoke or name them.

## Match the work

- **Small:** obvious local changes with known behavior, such as a header color, copy edit, or simple typo. Edit directly and perform a focused check. No full skill chain, delegation, design contest, task record, or mandatory independent review.
- **Routine:** bounded work with an understood boundary. Inspect what matters, implement, and run targeted checks. Add a supporting procedure or fresh review only when a concrete uncertainty or consequence warrants it.
- **Substantial/consequential:** multiple dependent components, uncertain integrations, shared-state changes, persistence or permission semantics, difficult logic, broad migrations, or other meaningful blast radius. Apply the relevant procedures below, delegate where a trigger in [Deliver](../deliver/SKILL.md) applies, and independently review the integrated change.

Classify by coupling, uncertainty, impact, and verification needs, not file count or keywords. Raise or lower depth as evidence changes. Do not ask the user to choose a tier. Explicit user direction governs process within platform permissions.

## Own the flow

Track the current outcome, constraints, and authorization. Research, planning, diagnosis, and review stay read-only unless implementation is requested. A later correction steers the active task; it is not automatic scope expansion. Casual conversation gets a normal answer.

For substantial work, read only procedures that materially apply:

- [Grill](../grill/SKILL.md) when the user asks to pressure-test an idea, or unresolved intent/product choices could materially change the outcome. Use it before technical design, not for every feature. Clear requirements and small edits skip it; investigate factual uncertainty instead of interviewing the user about it.
- [Ground](../ground/SKILL.md) when source behavior or integration assumptions need establishing.
- [Design](../design/SKILL.md) when callers, shared shapes, ownership, or an architectural choice need settling.
- [Diagnose](../diagnose/SKILL.md) for a defect or repeated failed acceptance condition.
- [Deliver](../deliver/SKILL.md) for implementation and coordination.
- [Verify](../verify/SKILL.md) for behavioral proof and evidence.
- [Review](../review/SKILL.md) for independent scrutiny of the integrated change.

These responsibilities overlap; they are not a mandatory serial ritual. Prove blocking boundaries before dependent fan-out. Main-agent work, explorers, independent workers, and independent checks should overlap: launch independent helpers in the same turn and keep the critical path moving while they run. Integrate continuously and verify once the work is in, not after each edit. When shared assumptions fail, stop affected work and correct the contract rather than adding workers.

Keep a compact task record only when dependencies or handoff make it useful. Record outcome, constraints, ownership, current artifact state, unresolved findings, and checks. Keep it in the authorized workspace, not global memory. Do not create records for trivial edits.

The session context supplies the configured role defaults (explorer, mechanical, worker, heavy_worker, reviewer, critical_reviewer) and any harness-specific mechanics. If unavailable, read [settings.json](../../settings.json). Explicitly select both model and effort for every helper when supported. Do not silently substitute an unavailable model. Use the selected parent as the disclosed fallback when appropriate; record that a preferred review model was unavailable. Do not change global model settings.

Conclude with the result and material evidence. Report unresolved checks honestly. Preserve the user's merge/deployment boundaries. Carry reviewer caveats and known limitations into the final report, and name the checks that were not run.
