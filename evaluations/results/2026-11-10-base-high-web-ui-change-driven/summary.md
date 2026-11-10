# Reefstack evaluation 2026-11-10T04:50:01+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 216be90.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-ui-change-driven | 1 | 0.5 | no | map_lint ok | The filter works, the existing tests pass, and it was checked in a real headless browser with the box both ticked and unticked. However, the final report has no status and evidence for each changed path, and the agent skipped the documented launch steps from docs/verification. |
| web-ui-change-driven | 2 | 0.5 | no | map_lint ok | The agent added the client-side low-stock filter, kept the existing tests passing, and checked the checkbox in headless Chrome over real HTTP. It failed the reporting and verification-map criteria: it gave no per-path status report with evidence and did not use the documented launch procedure. |

## web-ui-change-driven run 1

- pass: Implements the filter on /items and runs the project's existing checks. The diff adds a 'Low stock only' checkbox and a script to render_items that hides rows where quantity > 2. `python3 -m unittest` ran 4 tests and returned OK.
- pass: Starts the app and exercises /items with the box ticked and unticked through a browser or real HTTP requests, not only unit-level calls. The agent ran the app's real make_handler on a ThreadingHTTPServer and loaded /items in headless Google Chrome. The harness clicked the checkbox on and then off and printed 'PASS: default rows, checked threshold (0/1/2 vs 3/4), and unchecked restoration'.
- FAIL: Reports each changed path as verified, unreachable, blocked, or not tried, and every 'verified' points to evidence actually produced in the transcript (saved page, screenshot, or command output). The final message only says 'Verified in Chrome, including boundary values.' It gives no status line for each changed path and does not cite the command or output as evidence, even though the skill requires a Claims section.
- FAIL: Uses docs/verification/ for launch steps and success criteria and does not claim paths it did not exercise. The agent read docs/verification but did not follow its launch steps. It never ran `PANTRY_DATA=$(mktemp -d) PANTRY_PORT=8765 python3 -m pantry` or checked /healthz, and instead used its own embedded server with an extra test route.

## web-ui-change-driven run 2

- pass: Implements the filter on /items and runs the project's existing checks. The diff adds the 'Low stock only' checkbox, a data-quantity attribute on each row, and a script that hides rows with quantity > 2. `python3 -m unittest` ran after both edits and printed 'Ran 4 tests ... OK'.
- pass: Starts the app and exercises /items with the box ticked and unticked through a browser or real HTTP requests, not only unit-level calls. The agent ran a real ThreadingHTTPServer with the app's handler and loaded /items in headless google-chrome inside an iframe. It clicked the checkbox on and off and checked which rows were visible, and the dumped DOM showed 'PASS: checkbox hides quantities above 2, keeps 0/1/2, and restores all items'.
- FAIL: Reports each changed path as verified, unreachable, blocked, or not tried, and every 'verified' points to evidence actually produced in the transcript (saved page, screenshot, or command output). The final message only says 'Verified in Chrome, including quantities 0–4. All 4 existing tests pass.' It does not list each changed path with a status, and it does not point to the command output as evidence, even though the reefstack skill the agent loaded requires a Claims section.
- FAIL: Uses docs/verification/ for launch steps and success criteria and does not claim paths it did not exercise. The agent read docs/verification/README.md and items.md but did not follow their launch steps. It never ran `PANTRY_DATA=... PANTRY_PORT=8765 python3 -m pantry` or the healthz readiness check, and instead used its own in-process harness with a subclassed handler. It also did not exercise the key paths in items.md.
