---
name: reefstack
description: Route engineering work to a compact playbook, scale rigor to its consequences, and coordinate verified completion.
---

# Reefstack

Optimize time to verified completion while preserving correctness and maintainability. Keep the parent model and effort the user selected. Follow the user's intent and permissions: investigation and review remain read-only, and finishing local work does not authorize publication, merging, or deployment. Preserve concurrent work.

## Choose the procedure and the depth separately

- **Small, obvious work:** edit directly and perform a focused check. No playbook, full skill chain, delegation, task record, or mandatory independent review.
- **Routine, bounded work:** use the matching procedure when it helps, including a one-pass PR status check. Apply only relevant steps and targeted checks. Selecting a playbook does not require a record or delegation; use a record only for real dependencies or handoff.
- **Substantial or consequential work:** follow the matching playbook, create or reuse one [task record](../../references/task-record.md) before implementation edits or assignments, and obtain fresh independent review. Persistence guarantees, permissions, shared state, uncertain integrations, and difficult logic can be consequential even in one file.

Judge depth by coupling, uncertainty, impact, and verification needs, not file count or keywords. Adjust it as evidence changes. Do not ask the user to choose a tier.

## Dispatch to one compact playbook

Read the selected playbook before acting. Its steps own the task's sequence; supporting skills supply methods at the step that needs them. Use the existing task list or record for applicable steps and completion checks, with a short reason for a skipped step. Do not create a second tracker, force a tracker onto routine work, or run every playbook in sequence.

| Work | Playbook |
| --- | --- |
| Explain, investigate, compare, or diagnose without changes | [Investigation](../../references/playbooks/investigation.md) |
| Reproduce and fix a defect | [Bug fix](../../references/playbooks/bug-fix.md) |
| Add or change observable behavior | [Feature](../../references/playbooks/feature.md) |
| Change structure while preserving observable behavior | [Refactoring](../../references/playbooks/refactoring.md) |
| Improve a measured performance problem | [Performance](../../references/playbooks/performance.md) |
| Build a disposable experiment to decide an approach | [Prototype](../../references/playbooks/prototype.md) |
| Prepare and open or update an authorized pull request | [Opening a PR](../../references/playbooks/opening-pr.md) |
| Check, fix, or watch an existing PR | [PR follow-up](../../references/playbooks/pr-follow-up.md) |
| Land an explicitly authorized PR or ordered stack | [Shipping](../../references/playbooks/shipping.md) |
| Continue an existing task after handoff, interruption, or lost context | [Resume](../../references/playbooks/resume.md), then its original playbook's remaining steps |

A behavior-preserving migration is Refactoring; a read-only performance question is Investigation. Switch procedures only when the task changes within user authorization. A request to run Reefstack's own evaluation cases uses the existing [evaluation procedure](../../evaluations/playbook.md).

## Use supporting methods when needed

[Grill](../grill/SKILL.md) resolves consequential product choices or a requested pressure test; clear requirements skip it. [Ground](../ground/SKILL.md) establishes source-backed facts. [Design](../design/SKILL.md) settles caller contracts and ownership. [Diagnose](../diagnose/SKILL.md) isolates failure mechanisms. [Deliver](../deliver/SKILL.md) defines delegation and integration mechanics. [Verify](../verify/SKILL.md) defines adequate behavioral evidence, app driving, and verification-map checks. [Review](../review/SKILL.md) defines independent scrutiny and finding resolution. These are tools for the selected procedure, not a mandatory chain.

The session supplies role models, efforts, and host mechanics; otherwise read [settings.json](../../settings.json). Select both model and effort for helpers. Disclose unavailable models and any fallback; do not change global settings.

Keep the task record current at meaningful boundaries. For recorded work, finish its [readback and exact-link handoff](../../references/task-record.md#close-the-record-then-hand-it-off). Conclude with actual results, evidence, unresolved checks, and reviewer caveats. Never turn missing proof into a pass.
