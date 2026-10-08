---
name: verify
description: Verify requested engineering behavior on the relevant artifact and integration path, with revision-specific evidence and explicit coverage gaps.
---

# Verify

Read [the verification standard](../../references/verification.md) when choosing checks for substantial work. Reuse repository commands and the relevant runtime harness. Do not require a broad suite, build, new tests, or live service access for every edit.

Choose checks that would fail if the requested behavior or boundary assumption were wrong. For substantial work, exercise component contracts and the appropriate runtime surface, not only compilation or isolated functions. Capture actual results and compare them with independent expected values.

Verify artifacts returned by workers before accepting them. Tie receipts to the current code state and affected environment. Re-run the checks affected by subsequent edits; keep unchanged evidence when it remains valid.

When a required check is unavailable, identify the exact missing access, runtime, or fixture. Report blocked or unverified coverage and continue independent checks. Never weaken checks, invent results, or count a skipped check as passing. Hand material gaps to [review](../review/SKILL.md).
