---
name: reefstack
description: Use for any software engineering task in a code repository - fixing a bug or failing check, adding or changing a feature, refactoring, performance work, a prototype, investigating or explaining code, opening, checking, fixing, or watching a pull request, landing a PR, or resuming interrupted work. Picks the matching playbook and scales checks and review to the risk; small edits stay direct.
---

# Reefstack

Optimize time to verified completion while preserving correctness and maintainability. Keep the parent model and effort the user selected. Follow the user's intent, permissions, and repository instructions: investigation, planning, and review remain read-only unless changes are requested, and finishing local work does not authorize publication, merging, or deployment. Preserve concurrent work. No command or mode selection is required of the user.

**Helpers:** if you were started with a parent's brief, the brief governs. Do the assigned piece; do not select a playbook, spawn helpers, or request review unless the brief assigns that.

## Choose the procedure and the depth separately

- **Small, obvious work:** edit directly and perform a focused check. Local environment setup stays direct too. No playbook, full skill chain, delegation, or mandatory independent review.
- **Routine, bounded work:** use the matching procedure when it helps, including a one-pass PR status check. Apply only relevant steps and targeted checks; a routine change then gets a light fresh review. Selecting a playbook does not require delegation.
- **Substantial or consequential work:** follow the matching playbook and obtain a full fresh review aimed at the key fact. Persistence guarantees, permissions, shared state, uncertain integrations, and difficult logic can be consequential even in one file.
- **Quick, at the user's request:** focused checks only, with no reviewer or extra procedure; claims still carry evidence or a gap, and authorization and destructive-action limits still apply. A "quick question" asks for a short reply, not less process.

Judge depth by coupling, uncertainty, impact, and verification needs, not file count or keywords; when work may be consequential but its reach is unknown, measure it with [Blast radius](../blast-radius/SKILL.md). Adjust it as evidence changes. Do not ask the user to choose a tier.

## Dispatch to one compact playbook

Read the selected playbook before acting. Its steps own the task's sequence; supporting skills supply methods at the step that needs them. Use the existing task list for applicable steps and completion checks, with a short reason for a skipped step. Do not create a second tracker, force a tracker onto routine work, or run every playbook in sequence.

| Work | Playbook |
| --- | --- |
| Explain, investigate, compare, or diagnose without changes | [Investigation](references/playbooks/investigation.md) |
| Reproduce and fix a defect | [Bug fix](references/playbooks/bug-fix.md) |
| Add or change observable behavior | [Feature](references/playbooks/feature.md) |
| Change structure while preserving observable behavior | [Refactoring](references/playbooks/refactoring.md) |
| Improve a measured performance problem | [Performance](references/playbooks/performance.md) |
| Build a disposable experiment to decide an approach | [Prototype](references/playbooks/prototype.md) |
| Prepare and open or update an authorized pull request | [Opening a PR](references/playbooks/opening-pr.md) |
| Check, fix, or watch an existing PR | [PR follow-up](references/playbooks/pr-follow-up.md) |
| Land an explicitly authorized PR or ordered stack | [Shipping](references/playbooks/shipping.md) |
| Continue interrupted work, or take over someone else's branch, PR, or thread | [Resume](references/playbooks/resume.md), then the matching playbook's remaining steps |

A behavior-preserving migration is Refactoring; a read-only performance question is Investigation. Switch procedures only when the task changes within user authorization. A request to run Reefstack's own evaluation cases uses `evaluations/playbook.md` in the Reefstack repository.

## Use supporting methods when needed

[Grill](../grill/SKILL.md) resolves consequential product choices or a requested pressure test; clear requirements skip it. [Ground](../ground/SKILL.md) establishes source-backed facts. [Design](../design/SKILL.md) settles caller contracts and ownership. Blast radius finds what a change reaches beyond its own lines and the fact it is safe because of. [Diagnose](../diagnose/SKILL.md) isolates failure mechanisms. [Deliver](../deliver/SKILL.md) defines delegation and integration mechanics. [Verify](../verify/SKILL.md) defines adequate behavioral evidence, app driving, and verification-map checks. [Review](../review/SKILL.md) defines independent scrutiny and finding resolution. These are tools for the selected procedure, not a mandatory chain.

Before spawning helpers, read [delegation mechanics](harness/delegation.md); brief each with the [worker brief](references/worker-brief.md). After an authorized PR creation or push, follow PR follow-up's watch policy and schedule it with [PR watch](harness/pr-watch.md); honor status-only requests and paused watches. Choose each helper's model and effort for its work; do not change global settings.

Every non-trivial deliverable gets a fresh reviewer, scaled to its size. Before finishing, state the claims the change makes, each with evidence or a gap. Conclude with actual results, unresolved checks, and reviewer caveats. Never turn missing proof into a pass. Honor later user corrections and requests for more or less process.
