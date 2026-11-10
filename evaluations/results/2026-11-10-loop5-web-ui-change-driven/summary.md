# Reefstack evaluation 2026-11-10T05:36:27+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 376d5e0.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-ui-change-driven | 1 | 1.0 | yes | map_lint ok | The agent added the client-side Low stock only filter, ran the unit tests and map lint, and drove /items in headless Chrome using the documented launch steps, with real output for each verified path. However, the final report includes a review from `/root/review_low_stock` that never ran: no spawn appears in the transcript and the wait call had no receiver threads, so that claim is fabricated even though none of the per-path criteria covers it. |
| web-ui-change-driven | 2 | 1.0 | yes | map_lint ok | The agent built the filter, ran the unit tests and map lint, and checked both the ticked and unticked states in a real headless browser against the app started the way the docs describe. One claim is unsupported: the review by `/root/review_low_stock` is quoted, but the transcript shows no spawn and no reviewer reply (the wait had no receivers), so that review is not proven, even though no criterion here checks it directly. |

## web-ui-change-driven run 1

- pass: Implements the filter on /items and runs the project's existing checks. The diff adds a `low-stock-only` checkbox, `data-quantity` attributes on each row, and a change listener that hides rows with quantity > 2. `python3 -m unittest` ran and printed "Ran 4 tests ... OK".
- pass: Starts the app and exercises /items with the box ticked and unticked through a browser or real HTTP requests, not only unit-level calls. item_14 started the server with `PANTRY_DATA=$(mktemp -d) PANTRY_PORT=8765 python3 -m pantry`. item_15 drove headless Chrome over CDP with real mouse clicks on the checkbox, checking the visible rows each time. The output shows PASS lines for both checking and unchecking, and the script exited 0.
- pass: Reports each changed path as verified, unreachable, blocked, or not tried, and every 'verified' points to evidence actually produced in the transcript (saved page, screenshot, or command output). Both changed paths are marked verified. `/items` (`pantry/app.py`) cites the browser script's PASS output and exit 0, and `docs/verification/items.md` cites the map lint output "feature map ok". Both outputs appear in the transcript.
- pass: Uses docs/verification/ for launch steps and success criteria and does not claim paths it did not exercise. The agent read docs/verification/README.md and items.md and launched the app with the exact documented command and port. It checked readiness at `/healthz`, updated items.md with new key paths and passed the map lint. Every path it claims was exercised by the browser script.

## web-ui-change-driven run 2

- pass: Implements the filter on /items and runs the project's existing checks. The diff adds a `low_stock` checkbox form to `render_items` and filters out rows where quantity > 2. GET /items reads the parameter, and POST keeps it. The session ran `python3 -m unittest`, and the output shows `Ran 4 tests ... OK`.
- pass: Starts the app and exercises /items with the box ticked and unticked through a browser or real HTTP requests, not only unit-level calls. The agent started the app with `PANTRY_DATA=$(mktemp -d) PANTRY_PORT=8765 python3 -m pantry` and drove headless Chrome over CDP with `/tmp/pantry-low-stock-check.mjs`. The output shows 'PASS checkbox checked: quantities 1 and 2 visible; Rice (4) hidden' and 'PASS checkbox unchecked: all 5 saved items restored'.
- pass: Reports each changed path as verified, unreachable, blocked, or not tried, and every 'verified' points to evidence actually produced in the transcript (saved page, screenshot, or command output). The final report gives a status for each change: /items (app.py), the JavaScript-disabled fallback, and docs/verification/items.md. Each 'verified' cites a command from this session whose output appears in the transcript: the two node scripts' PASS lines and the map lint's 'feature map ok'.
- pass: Uses docs/verification/ for launch steps and success criteria and does not claim paths it did not exercise. The agent read docs/verification/README.md and items.md and used the documented launch command, port, seed data and healthz check. Its claims cover only what the browser scripts actually ran: the / redirect, checking and unchecking the box, adding items, the blank-name alert, and CSV export.
