---
name: verify
description: Verify requested engineering behavior on the relevant artifact and integration path, with revision-specific evidence and explicit coverage gaps.
---

# Verify

Read [the verification standard](../../references/verification.md) when choosing checks for substantial work. Reuse repository commands and the relevant runtime harness. Do not require a broad suite, build, new tests, or live service access for every edit.

Choose checks that would fail if the requested behavior or boundary assumption were wrong. For substantial work, exercise component contracts and the appropriate runtime surface, not only compilation or isolated functions. Capture actual results and compare them with independent expected values.

Time checks to the work. While building, run only the cheapest check that unblocks the next step. Once all work is in and the diff is stable, run the focused tests and the CI-equivalent suites for the changed code in one pass. Do not rerun the full set after each small fix; rerun what the fix affects.

An instruction to skip tests covers the request it was given for. Before opening or updating a pull request, run the focused tests for changed files, or say plainly that tests were not run and CI may fail.

Verify artifacts returned by workers before accepting them. Tie receipts to the current code state and affected environment. Re-run the checks affected by subsequent edits; keep unchanged evidence when it remains valid.

When a required check is unavailable, identify the exact missing access, runtime, or fixture. Report blocked or unverified coverage and continue independent checks. Never weaken checks, invent results, or count a skipped check as passing. Hand material gaps to [review](../review/SKILL.md). The final report names the checks that were not run and carries reviewer caveats and known limitations.
