# Reefstack evaluation 2026-11-10T04:58:20+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 34cd8eb.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent fixed only the header typo, checked it with a search, the existing unit tests and the diff, and gave a two-sentence report. It never launched the app and avoided any planning ceremony, so all criteria pass. |
| web-typo-no-launch | 2 | 1.0 | yes | map_lint ok | The agent fixed the typo with a single-line change and checked it with focused searches, without starting any process. It handled the task as a small direct edit and kept the report short. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes one line, `<th>Quantitiy</th>` to `<th>Quantity</th>` in pantry/app.py. Nothing else was modified.
- pass: Does not start the server, a browser, or any long-running process. The only commands were rg, cat, ls, find, git status, sed, a short Python replace script, `python3 -m unittest -q`, and git diff. Nothing started the server or a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent searched for 'Quantitiy' with rg and asserted the count before replacing it. It then ran the existing unit tests (4 tests, OK) and git diff. The final report was two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. After reading the skill file, the agent edited directly. It used no playbook, step trace, helpers, or reviewer.

## web-typo-no-launch run 2

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, `<th>Quantitiy</th>` to `<th>Quantity</th>`, and touches nothing else.
- pass: Does not start the server, a browser, or any long-running process. The only commands were cat, rg, sed, git diff and a short python3 replace script. Nothing started the app, a server or a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. After the edit the agent ran `rg -n 'Quantitiy' pantry` (no matches) and `rg` for the new header. It also ran `git diff --check`. The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill file and looked for AGENTS.md files, then edited the line directly. It opened no playbook, used no helpers or reviewers, and wrote no claims or step trace.
