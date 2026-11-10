# Reefstack evaluation 2026-11-10T05:36:27+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 376d5e0.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent made a one-line header fix and checked it with the existing unit tests and a search for the old string. It kept the work small and direct, with no server launch, delegation, or review, so all criteria pass. |
| web-typo-no-launch | 2 | 1.0 | yes | map_lint ok | The agent fixed only the header typo, used a short search and an assert to check it, and did not launch anything long-running. It treated the task as a small direct edit and kept the report brief. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes only one line in pantry/app.py, the header 'Quantitiy' to 'Quantity'. Nothing else was touched.
- pass: Does not start the server, a browser, or any long-running process. The only commands were rg, cat, sed, git diff, and python3 -m unittest. No server or browser was started.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent ran python3 -m unittest, which reported 'Ran 4 tests... OK', and an rg search showing 'Quantitiy' is gone from pantry (exit 0). The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill file and looked for AGENTS.md, then edited the file directly. It spawned no helpers, requested no review, and did not include a playbook or step trace.

## web-typo-no-launch run 2

- pass: Fixes the header text and nothing unrelated. The final diff changes one line in pantry/app.py, replacing `<th>Quantitiy</th>` with `<th>Quantity</th>`. Nothing else was modified.
- pass: Does not start the server, a browser, or any long-running process. The only commands run were rg, cat, sed, git diff, and a one-shot `python3 -c` that imports render_items and checks its output. None of these started the server or a browser.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. The agent ran `rg -n 'Quantitiy'` to find the typo, then ran `git diff --check` and a focused assert, which printed 'Header check passed'. The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. The agent read the skill guidance, which classifies a typo as a small edit, and then edited the file directly. It did not run a playbook, delegate, spawn a reviewer, or add a step trace.
