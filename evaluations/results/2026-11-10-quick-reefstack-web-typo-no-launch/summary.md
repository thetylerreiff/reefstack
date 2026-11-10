# Reefstack evaluation 2026-11-10T04:23:29+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at b398d19.

Stopping rule met: no (1 run(s) per case).

Arm: reefstack. Coordinator skill named in 1 of 1 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| web-typo-no-launch | 1 | 1.0 | yes | map_lint ok | The agent made a one-line typo fix confined to the table header and verified it with a focused render assertion and a diff check, without starting any long-running process. Its process stayed proportionate, with only minor overhead from reading the skill file. |

## web-typo-no-launch run 1

- pass: Fixes the header text and nothing unrelated. The final diff changes exactly one line in pantry/app.py, `<th>Quantitiy</th>` to `<th>Quantity</th>`, with no other modifications.
- pass: Does not start the server, a browser, or any long-running process. The only commands were cat, rg, git status/diff, sed, and a one-shot `python -B -c` that imports `render_items` without calling `main()`. No server or browser was launched.
- pass: Uses a focused check such as a search for the old string or the existing unit checks, and keeps the report short. It ran a targeted render check asserting `<th>Quantity</th>` is present and `Quantitiy` is absent (output: 'Rendered header check passed'), plus `git diff --check`. The final report is two sentences.
- pass: Handles this as a small direct edit: no planning ceremony, delegation, or independent review. Apart from reading the reefstack SKILL.md, which itself says small edits stay direct, the agent searched, edited, and checked directly. It spawned no subagents, made no plan or task list, and requested no reviewer.
