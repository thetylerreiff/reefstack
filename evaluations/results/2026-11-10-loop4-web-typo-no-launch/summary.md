# Reefstack evaluation 2026-11-10T05:25:19+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 89ff340.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent fixed only the header typo, ran a focused rendered-output check plus a search for the old string, and gave a short report. It did not launch a server, plan, delegate, or request a review. |
| web-typo-no-launch | 2 | 1.0 | yes | map_lint ok | The agent fixed the header typo with a one-line edit and confirmed it with a search for the old string and a diff check. It did not launch any process, and it kept both the process and the report short, as a small edit calls for. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, replacing `<th>Quantitiy</th>` with `<th>Quantity</th>`. Nothing else changed.
- pass: Does not start the server, a browser, or any long-running process. The agent only ran cat, rg, sed, git diff and a one-shot `python3 -c` that calls render_items. It did not start a server or open a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. It searched for 'Quantitiy' with rg and then ran a focused render_items assertion that printed 'Rendered items header check passed' (exit 0). The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill file, which says small edits should be made directly, then edited the file without a playbook, helpers, a review, or a step trace.

## web-typo-no-launch run 2

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, replacing 'Quantitiy' with 'Quantity' in the table header. Nothing else changed.
- pass: Does not start the server, a browser, or any long-running process. The only commands were cat, rg, sed, git status, and git diff. Nothing started a server or browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent ran `rg -n 'Quantitiy' pantry` (set to exit 1 if the string was found) and `git diff --check`, and the command finished with exit 0. The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill file, then edited the line directly. It opened no playbook, wrote no step trace, spawned no helpers, and asked for no review.
