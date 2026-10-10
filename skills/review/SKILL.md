---
name: review
description: Obtain and assess fresh independent review for substantive engineering changes, tracing material findings and rechecking accepted fixes.
---

# Review

Use [the review rubric](../../references/review-rubric.md) for relevant correctness, integration, security, and maintainability risks. A tiny known local edit does not require this procedure or a reviewer agent.

For substantial implementation, spawn a fresh read-only reviewer with intent, the current diff, relevant surrounding source, acceptance criteria, and verification evidence. For a user-facing change, include the per-path verification report and the `docs/verification/` files for the features the diff touches, so the reviewer can compare them. Start it only after every worker has sent its final result and edits have stopped; if the diff changes before you report the verdict, have the reviewer recheck the changed areas first. Avoid supplying a persuasive implementation narrative. Use the `reviewer` role, or `critical_reviewer` when the change touches authentication, permissions, migrations, money, or data deletion. Select both model and effort explicitly when supported. Different models from the same vendor are not cross-vendor diversity.

If the preferred reviewer cannot run, disclose that limitation and use an available fresh reviewer when adequate. If no independent reviewer is available, perform a focused self-check and label independent review unverified; do not claim that the full loop passed.

A stale map entry is fixed in the same change, never deferred: update the feature file to the new entry point, run the map lint with `--since <base>`, drive the new entry point, and have the reviewer recheck those files. Unexercised or unsupported paths go back to [verify](../verify/SKILL.md) or are reported as gaps; they are not reworded into passes.

When the same finding or failure appears a second time, follow [enforcement](../../references/enforcement.md): propose the check that makes it fail automatically, and record it in the project's failure log if one exists.

Read findings and trace evidence yourself. Fix material accepted findings, explain dismissals, rerun affected checks, and recheck the changed areas once. Repeat a full review only for P1, security, authorization, or data-loss findings. A proved lone finding matters. Do not manufacture nits or repeat an unchanged complete review after every local correction.

In a user-requested review, remain read-only and lead with actionable findings and file/line evidence. Review authorization alone is not implementation authorization.
