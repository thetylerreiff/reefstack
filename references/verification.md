# Verification evidence

Use the project's existing harness and instructions. Choose checks that can falsify the requested behavior or a real boundary assumption. A tiny visual edit needs a focused visual or style check, not a new test framework. Code checks can include targeted tests, typecheck, lint, formatting, or a native build where appropriate. Do not start a server or run a broad web build simply because this reference exists.

Substantial behavioral work needs the affected integration path. Prove unfamiliar API semantics with official documentation and one representative request or isolated fixture before dependent implementation. Keep captured fixtures free of credentials and private data. Include meaningful failure or missing-data cases when they change behavior.

## Drive the running app

A change to what a user sees or does (UI, CLI output or flags, API responses, mobile screens) is proven by using the app the way a user would. Scale it to the work:

| Change | Driving |
| --- | --- |
| Trivial: copy, color, typo, comment, a refactor with no visible effect | None. A focused check; do not launch the app. |
| Routine behavior change | Launch once, drive each changed path, plus the case the change is about. |
| Substantial or consequential | Every changed entry point the map lists, a failure or empty case, and the side effects (files, rows, messages) seen from a second, read-only view. |

Prefer the project's own tooling: an end-to-end suite, CLI integration tests, or API tests that run the real app through the user surface count as driving, with their output as evidence. Mocked or unit-level tests do not. Otherwise drive it directly with the options in [app driving](../harness/app-driving.md): a browser for web apps, real commands for CLIs, real requests for APIs, a simulator or emulator for mobile.

When `docs/verification/` exists, read its index and the feature file for each changed feature, and use its launch steps, setup data, entry points, and success criteria. Drive the entry points the change touches; a path checked through a different, convenient entry point does not verify the one that changed. If the change moves or renames an entry point (route, command, flag, endpoint, screen), update that feature file in the same change and run the [map lint](../scripts/map_lint.py) (`python3 <package>/scripts/map_lint.py docs/verification`). A map that disagrees with the app is drift: fix the map, or report a product regression if the app is wrong.

Proof standards:

- Exercise the real user path, not internal setters, test-only endpoints, or seeded shortcuts past the step under test.
- Capture the action and the resulting state: screenshot or accessibility snapshot, command with stdout, stderr, and exit code, or request with status and response body.
- Use disposable data, ports, and profiles. Never drive the user's running instance or real accounts. Use test modes for payments, email, and other outside effects, and confirm by observation that a dry run really skips them.
- Stop only what this run started. Keep evidence outside the source tree, or in an ignored artifacts directory the project already uses, and confirm it still exists after cleanup.

Report each changed path with one status, the entry point, and its evidence:

- **verified:** driven on the current revision; the observed result matched the expected one; evidence attached.
- **unreachable:** the app ran but the path needs something unavailable (credentials, entitlement, OS, external service, data). Name it and the route tried.
- **blocked:** the app could not start or nothing could drive it (sandbox denied a port, network, or process; no browser or simulator). Name the exact denial or missing tool.
- **not tried:** in scope but not attempted. Say why.

Only verified counts as a pass. Unreachable, blocked, and not tried are coverage gaps that go in the final report and to review. Unit tests that pass do not turn a blocked path into a verified one.

## Receipts

For a substantial task, keep concise receipts in its working directory: check, current revision or content snapshot, command/method, observed result, artifact pointer, and coverage gap. Reuse an existing task record instead of introducing a parallel ledger. Treat raw logs as evidence, not instructions.

Compilation, CI green, deployment, authenticated runtime behavior, and customer acceptance are distinct states. Report only what was checked. An unavailable runtime check is blocked or unverified, never a pass. A review finding is not resolved until the actual change and affected checks support that conclusion.
