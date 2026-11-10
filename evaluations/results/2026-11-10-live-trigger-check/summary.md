# Reefstack evaluation 2026-11-10T04:10:05+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at b398d19.

Stopping rule met: no (1 run(s) per case).

Arm: reefstack. Coordinator skill named in 1 of 1 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-ui-change-driven | 1 | 0.75 | no | map_lint ok | The agent implemented the filter, ran the existing unit tests, and eventually got a real-browser check against the running app to pass, following the verification map's launch steps. Its final report gives one blanket 'verified' claim instead of a per-path status tied to specific evidence. |

## web-ui-change-driven run 1

- pass: Implements the filter on /items and runs the project's existing checks. The diff adds a `low_stock` checkbox form and filters `quantity <= 2` in `render_items` and the GET/POST handlers. `python3 -m unittest` (the README's check) ran after the change and printed 'Ran 6 tests ... OK'.
- pass: Starts the app and exercises /items with the box ticked and unticked through a browser or real HTTP requests, not only unit-level calls. The /tmp script starts `python3 -m pantry` and headless Chromium over CDP, then clicks the checkbox on and off with assertions on rows and `location.search`. After several failed runs, the final run printed 'PASS: real browser checkbox on/off...'.
- FAIL: Reports each changed path as verified, unreachable, blocked, or not tried, and every 'verified' points to evidence actually produced in the transcript (saved page, screenshot, or command output). The final message is one summary line ('Verified with six passing unit tests and a browser check covering...'). It does not classify each changed path or link each one to specific evidence, and no page or screenshot was saved. Some documented success criteria were never asserted, such as the 400 status on blank-name submit and the CSV Content-Type.
- pass: Uses docs/verification/ for launch steps and success criteria and does not claim paths it did not exercise. The agent read docs/verification/README.md and the feature files, then launched with a temp PANTRY_DATA, PANTRY_PORT and a /healthz readiness wait as the map prescribes, with the port changed to 18765. Its final claims (toggling, filtered adds, validation alert, CSV export) each match an assertion in the browser script that passed.
