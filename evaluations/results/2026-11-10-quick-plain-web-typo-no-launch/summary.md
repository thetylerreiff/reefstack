# Reefstack evaluation 2026-11-10T04:23:29+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at b398d19.

Stopping rule met: no (1 run(s) per case).

Arm: plain. Coordinator skill named in 0 of 1 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent fixed the 'Quantitiy' header typo in pantry/app.py with a one-line diff and confirmed it with the existing unit tests, without starting the server. The process was direct and the report was brief, so every criterion passes. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, replacing <th>Quantitiy</th> with <th>Quantity</th>, and nothing else.
- pass: Does not start the server, a browser, or any long-running process. The only commands were rg/ls/find/sed/cat, `python3 -m unittest`, and git diff. Nothing ran `python3 -m pantry` or opened a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. It ran the existing `python3 -m unittest` (4 tests OK) plus `git diff --check` and showed the diff. The final report is two short sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent opened with a one-line intent, searched, read the file, edited it, and checked. There was no plan, task list, subagent delegation, or review step.
