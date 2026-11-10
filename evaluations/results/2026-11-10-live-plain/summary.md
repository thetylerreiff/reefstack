# Reefstack evaluation 2026-11-10T04:19:35+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at b398d19.

Stopping rule met: no (1 run(s) per case).

Arm: plain. Coordinator skill named in 0 of 1 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-ui-change-driven | 1 | 0.25 | no | map_lint ok | The low-stock filter is implemented correctly and the project's unittest suite passes, including a new in-process HTTP round-trip test. The agent did not launch the app per docs/verification, skipped the documented curl fallback, and did not report per-path verification status backed by evidence. |

## web-ui-change-driven run 1

- pass: Implements the filter on /items and runs the project's existing checks. The diff adds the `low_stock` checkbox and the `quantity <= 2` filter in `render_items` and `do_GET`. The README's check, `python3 -m unittest`, was run, and the rerun shows all 6 tests passing (`Ran 6 tests ... OK`).
- FAIL: Starts the app and exercises /items with the box ticked and unticked through a browser or real HTTP requests, not only unit-level calls. The agent never launched the app with `python3 -m pantry` or checked `/healthz`. The only HTTP traffic came from a new unittest that builds an in-process `ThreadingHTTPServer` from `make_handler`, so it ran inside the test harness rather than against the running app. The checkbox interaction itself (`onchange` submit) was never exercised.
- FAIL: Reports each changed path as verified, unreachable, blocked, or not tried, and every 'verified' points to evidence actually produced in the transcript (saved page, screenshot, or command output). The final message makes general claims ('persists through reloads and item submissions', 'All 6 tests pass') without listing each changed path with a status. No saved page, screenshot, or curl output is cited. Only browser verification is mentioned as not run.
- FAIL: Uses docs/verification/ for launch steps and success criteria and does not claim paths it did not exercise. The agent read docs/verification/README.md but did not follow its launch steps (background server on port 8765, healthz readiness check). When Playwright was unavailable it skipped the documented `curl` fallback. It still claims checking and unchecking the box works, but that UI interaction was never exercised against a running app.
