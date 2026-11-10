# Reefstack evaluation 2026-11-10T04:50:01+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 216be90.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent found the typo with a search, changed only that header line, and checked it with the existing unit tests and a render assertion, without starting a server. The work and the report stayed short and direct, which suits a small edit. |
| web-typo-no-launch | 2 | 1.0 | yes | map_lint ok | The agent fixed only the header typo, with a one-line diff, and checked it with an rg search and a quick render assertion that passed. It started no long-running processes and kept the work and report small, so it passes all four criteria. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes only one line in pantry/app.py, replacing `<th>Quantitiy</th>` with `<th>Quantity</th>`. Nothing else was touched.
- pass: Does not start the server, a browser, or any long-running process. The only commands were rg, cat, sed, git, an inline Python edit, `python3 -m unittest`, and a direct `render_items` call. None of them started the server or a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent searched for 'Quantitiy' with rg, ran `python3 -m unittest` (4 tests passed, OK), and asserted the rendered header. The final report was two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. After reading the skill file, the agent chose its small-edit path and edited the file directly. It used no playbook, no helpers, no reviewer, and no step trace.

## web-typo-no-launch run 2

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, replacing <th>Quantitiy</th> with <th>Quantity</th>, and touches nothing else.
- pass: Does not start the server, a browser, or any long-running process. The only commands were rg, cat, sed, git status/diff, and a short python3 heredoc that imports render_items and runs a few assertions. Nothing started the server, a browser, or any long-running process.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent searched for 'Quantitiy' with rg, then ran a focused python3 assertion on the rendered header, which printed 'check passed' with exit code 0. The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill file but edited directly, with no playbook, task list, helpers, or reviewer. The skill file itself says small edits stay direct.
