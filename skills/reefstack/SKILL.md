---
name: reefstack
description: Use for any software engineering task in a code repository - fixing a bug or failing check, adding or changing a feature, refactoring, performance work, a prototype, investigating or explaining code, opening, checking, fixing, or watching a pull request, landing a PR, or resuming interrupted work. Picks the matching playbook and scales checks and review to the risk; small edits stay direct.
---

# Reefstack

Optimize time to verified completion while preserving correctness and maintainability. Follow the user's intent, permissions, and repository instructions: investigation, planning, and review stay read-only unless changes are requested, and finishing local work does not authorize publication, merging, or deployment. Keep the model and effort the user selected. Preserve concurrent work.

**Helpers:** if you were started with a parent's brief, the brief governs. Do the assigned piece; do not select a playbook, spawn helpers, or request review unless the brief assigns that.

## First decide: small edit or not

A **small edit** changes nothing a user can do or observe beyond wording or appearance: a typo, copy, color, comment, formatting, or a config value, at a known location. Edit directly, run a focused check (search for the old text, run the existing tests), do not launch the app, and answer in one or two sentences. No playbook, trace, delegation, or review.

**Everything else is not small, however few lines it touches.** Adding, removing, or renaming a control, command, flag, route, field, or output, or changing what one does, is at least routine. For such work two things are mandatory:

1. **Open the playbook.** Before the first edit, read the matching playbook file from the table below (paths are relative to this file's folder) and follow its steps. This file does not replace it.
2. **Finish with proof.** End the final report with the Claims, Review, and Step trace described at the end of this file.

## Depth

- **Routine, bounded work:** follow the playbook. Skip a step that does not apply, with a short reason; use targeted checks, then a light fresh review. A playbook does not require delegation.
- **Substantial or consequential work:** follow the playbook and obtain a full fresh review aimed at the key fact. Persistence guarantees, permissions, shared state, uncertain integrations, and difficult logic can be consequential even in one file.
- **Quick, at the user's request:** focused checks only, with no reviewer; claims still carry evidence or a gap, and authorization limits still apply. A "quick question" asks for a short reply, not less process.

Judge depth by coupling, uncertainty, impact, and verification needs, not file count; when reach is unknown, measure it with [Blast radius](../blast-radius/SKILL.md). Adjust as evidence changes. Do not ask the user to choose a tier. Local environment setup stays direct.

## Playbooks

Use the existing task list for the playbook's steps; do not create a second tracker or run every playbook in sequence.

| Work | Playbook |
| --- | --- |
| Explain, investigate, compare, or diagnose without changes | [Investigation](references/playbooks/investigation.md) |
| Reproduce and fix a defect | [Bug fix](references/playbooks/bug-fix.md) |
| Add or change observable behavior, including renaming an entry point | [Feature](references/playbooks/feature.md) |
| Change structure while preserving every entry point and output | [Refactoring](references/playbooks/refactoring.md) |
| Improve a measured performance problem | [Performance](references/playbooks/performance.md) |
| Build a disposable experiment to decide an approach | [Prototype](references/playbooks/prototype.md) |
| Prepare and open or update an authorized pull request | [Opening a PR](references/playbooks/opening-pr.md) |
| Check, fix, or watch an existing PR | [PR follow-up](references/playbooks/pr-follow-up.md) |
| Land an explicitly authorized PR or ordered stack | [Shipping](references/playbooks/shipping.md) |
| Continue interrupted work, or take over someone else's branch, PR, or thread | [Resume](references/playbooks/resume.md), then the matching playbook's remaining steps |

A read-only performance question is Investigation. Switch procedures only when the task changes within user authorization. A request to run Reefstack's own evaluation cases uses `evaluations/playbook.md` in the Reefstack repository.

## Supporting methods

[Grill](../grill/SKILL.md) resolves consequential product choices. [Ground](../ground/SKILL.md) establishes source-backed facts. [Design](../design/SKILL.md) settles caller contracts and ownership. Blast radius finds what a change reaches. [Diagnose](../diagnose/SKILL.md) isolates failure mechanisms. [Deliver](../deliver/SKILL.md) defines delegation and integration. [Verify](../verify/SKILL.md) defines behavioral evidence, app driving, and verification-map checks. [Review](../review/SKILL.md) defines independent scrutiny. Playbook steps say when to use them.

Before spawning helpers, read [delegation mechanics](harness/delegation.md); brief each with the [worker brief](references/worker-brief.md). After an authorized PR creation or push, follow PR follow-up's watch policy and schedule it with [PR watch](harness/pr-watch.md); honor status-only requests and paused watches. Choose each helper's model and effort for its work; do not change global settings. Honor later user corrections and requests for more or less process.

## Finish with proof

Beyond a small edit, the final report ends with these three parts:

- **Claims:** one line per changed path: each entry point the change touches (page, command, endpoint) and each changed doc, map, or test file, status first: verified, unreachable, blocked, or not tried. Verified needs evidence produced in this session on the current code through the app's real entry point, started the way the project documents it (`docs/verification/` launch steps when present): quote the exact command or request as run (with any environment variables it set), the output lines that show the result, and the exit code or status. Cite a file only if this session wrote it and printed it. "Checks passed" is a summary, not evidence; never turn missing proof into a pass.
- **Review:** `Review: not run (<reason>)` unless spawning returned a reviewer and you received its reply; then give its findings, each accepted or rejected with a reason. A spawn that returned an error started nothing: do not wait on it or report a result for it. Never report a review, check, or file this session cannot point to.
- **Step trace:** a `Playbook: <name>` line, then one numbered line per step of that playbook: the step's output name and what it holds, or `skipped: <reason>`. A step that ran again is listed again, followed by every step built on it. Pipe the draft report to `python3 scripts/graph_trace.py -` in this skill's folder and fix what it reports before finishing.
