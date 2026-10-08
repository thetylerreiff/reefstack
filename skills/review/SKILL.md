---
name: review
description: Obtain and assess fresh independent review for substantive engineering changes, tracing material findings and rechecking accepted fixes.
---

# Review

Use [the review rubric](../../references/review-rubric.md) for relevant correctness, integration, security, and maintainability risks. A tiny known local edit does not require this procedure or a reviewer agent.

For substantial implementation, spawn a fresh read-only reviewer with intent, the current diff, relevant surrounding source, acceptance criteria, and verification evidence. Avoid supplying a persuasive implementation narrative. Use the configured reviewer role; a routine warranted review can use the routine_reviewer role. Select both model and effort explicitly when supported. Different models from the same vendor are not cross-vendor diversity.

If the preferred reviewer cannot run, disclose that limitation and use an available fresh reviewer when adequate. If no independent reviewer is available, perform a focused self-check and label independent review unverified; do not claim that the full loop passed.

Read findings and trace evidence yourself. Fix material accepted findings, explain dismissals, rerun affected checks, and recheck the changed areas. A proved lone finding matters. Do not manufacture nits or repeat an unchanged complete review after every local correction.

In a user-requested review, remain read-only and lead with actionable findings and file/line evidence. Review authorization alone is not implementation authorization.
