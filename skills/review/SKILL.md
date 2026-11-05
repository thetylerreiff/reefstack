---
name: review
description: Obtain and assess fresh independent review for every non-trivial deliverable, scaled to its size, tracing material findings and rechecking accepted fixes.
---

# Review

Use [the review rubric](../reefstack/references/review-rubric.md) for relevant correctness, integration, security, and maintainability risks. A tiny known local edit, a change the user asked to make quick, a verification map written on request, and a disposable prototype do not require a reviewer unless the user asks.

## When and how much

Every non-trivial deliverable gets a fresh read-only reviewer once it is integrated, every worker has sent its final result, and edits have stopped. The unit is a deliverable the user would recognize (a fix, a feature, a PR), not each internal milestone or worker piece. A review cadence the user states overrides this default.

- **Routine change:** give the reviewer the stated intent, the diff, and the claims from [verify](../verify/SKILL.md). Ask it to check the intended case and broken callers.
- **Large or risky change:** also give relevant surrounding source, acceptance criteria, verification evidence, and the key fact the change is safe because of, with the risks [blast radius](../blast-radius/SKILL.md) found when it ran. Ask the reviewer to try to break that fact, running a check where it can rather than only reading. For a user-facing change, include the per-path verification report and the `docs/verification/` files for the features the diff touches. Changes to authentication, permissions, migrations, money, or data deletion are risky whatever their size.

Avoid supplying a persuasive implementation narrative. If late edits that are not responses to findings change the diff before you report the verdict, have the reviewer recheck those areas. If no independent reviewer is available, perform a focused self-check and label independent review unverified; do not claim that the full loop passed. A reviewer that times out or returns nothing has not approved.

## Resolve findings

Read findings and trace evidence yourself. Judge each finding's severity yourself, whatever label it came with: a rare path, a small cost, or an extra guard is P3. Accept or reject every finding with a one-line reason; nothing is silently dropped. Fix accepted findings with the smallest change, preferring one that deletes or narrows code. If fixes grew the diff, cut before adding more. List declined out-of-scope items as follow-ups.

After fixing a P1 or P2, rerun affected checks and have a reviewer recheck the changed areas once. Repeat a full review only for security, authorization, or data-loss findings. Do not repeat an unchanged review after every local correction.

When the same bug or finding appears a second time, sweep the whole class once instead of fixing the next instance, and follow [enforcement](../reefstack/references/enforcement.md): propose the check that makes it fail automatically, and record it in the project's failure log if one exists.

A stale map entry is fixed in the same change, never deferred: update the feature file to the new entry point, run the map lint with `--since <base>`, drive the new entry point, and have the reviewer recheck those files. Unexercised or unsupported paths go back to [verify](../verify/SKILL.md) or are reported as gaps; they are not reworded into passes.

In a user-requested review, remain read-only and lead with actionable findings and file/line evidence. Review authorization alone is not implementation authorization.

Before spawning a helper, read the host's [delegation mechanics](../reefstack/harness/delegation.md) and brief it with the [worker brief](../reefstack/references/worker-brief.md).
