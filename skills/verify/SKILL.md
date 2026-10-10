---
name: verify
description: Verify requested engineering behavior on the relevant artifact and integration path, including driving the running app for user-facing changes, with revision-specific evidence and explicit coverage gaps.
---

# Verify

Read [the verification standard](../../references/verification.md) when choosing checks for substantial work or any user-facing behavior change. Reuse repository commands and the relevant runtime harness. Do not require a broad suite, build, new tests, or live service access for every edit.

Choose checks that would fail if the requested behavior or boundary assumption were wrong. For substantial work, exercise component contracts and the appropriate runtime surface, not only compilation or isolated functions. Capture actual results and compare them with independent expected values.

## Drive the app for user-facing changes

When a routine or larger change alters what a user sees or does through a UI, CLI, or API, start the app and use the changed paths as a user would: a browser for web apps, real commands for CLIs, real requests for APIs, a simulator for mobile. Prefer the project's own end-to-end tooling; [app driving](../../harness/app-driving.md) lists options per project type. Trivial edits (copy, color, typo, no visible behavior change) get a focused check and no launch.

If `docs/verification/` exists, use its feature files for launch, setup, entry points, and success criteria. When the change moves an entry point, update the map in the same change and run the [map lint](../../scripts/map_lint.py).

Report each changed path as verified, unreachable (with the reason), blocked, or not tried, with its evidence: screenshots, command output, or saved responses. A sandbox that blocks the launch, or a missing driver, is blocked, never a pass.

## Timing and receipts

Time checks to the work. While building, run only the cheapest check that unblocks the next step. Once all work is in and the diff is stable, run the focused tests, the CI-equivalent suites for the changed code, and the app drive in one pass. Do not rerun the full set after each small fix; rerun what the fix affects.

An instruction to skip tests covers the request it was given for. Before opening or updating a pull request, run the focused tests for changed files, or say plainly that tests were not run and CI may fail.

Verify artifacts returned by workers before accepting them. Tie receipts to the current code state and affected environment. Re-run the checks affected by subsequent edits; keep unchanged evidence when it remains valid.

When a required check is unavailable, identify the exact missing access, runtime, or fixture. Report blocked or unverified coverage and continue independent checks. Never weaken checks, invent results, or count a skipped check as passing. Hand material gaps to [review](../review/SKILL.md). The final report names the checks that were not run and carries reviewer caveats and known limitations.
