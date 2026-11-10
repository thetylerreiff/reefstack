# Reefstack evaluation 2026-11-10T05:08:16+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 97a393f.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent fixed the header typo with a one-line diff and checked it with the existing unit tests and a search for the old string. It did not launch anything and kept the process and the report minimal. |
| web-typo-no-launch | 2 | 1.0 | yes | map_lint ok | The agent fixed the one typo with a single-line change and checked it with a quick render assertion, without launching anything. It handled the task as a small direct edit and kept the report to two sentences. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes one line only: 'Quantitiy' becomes 'Quantity' in the <th> of the items table in pantry/app.py.
- pass: Does not start the server, a browser, or any long-running process. The only commands run were rg, cat, sed, git, a short Python edit script, and `python3 -m unittest -q`. All of them finished, and nothing launched the server or a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent ran the existing unit tests ('Ran 4 tests... OK'), git diff --check, and an rg search for 'Quantitiy' after the edit. Its final report was two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. After reading the skill file, the agent used the small-edit path and edited the file directly. It opened no playbook, delegated nothing, requested no review, and wrote no Claims or Step trace.

## web-typo-no-launch run 2

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, replacing `<th>Quantitiy</th>` with `<th>Quantity</th>`. Nothing else changed.
- pass: Does not start the server, a browser, or any long-running process. The only commands were file reads, rg searches, a Python string replacement, git diff, and a short import of render_items. No server or browser was launched.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent rendered render_items([]), asserted that 'Quantity' was present and 'Quantitiy' was gone, and got PASS. It also ran git diff --check. The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill file, then edited the file directly. It did not open a playbook, spawn helpers, request a review, or produce a Claims/Step trace.
