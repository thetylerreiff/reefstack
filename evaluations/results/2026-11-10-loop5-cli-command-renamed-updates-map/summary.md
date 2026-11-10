# Reefstack evaluation 2026-11-10T05:36:27+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 376d5e0.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| cli-command-renamed-updates-map | 1 | 1.0 | yes | map_lint ok, map_current ok | The agent renamed the command, updated the README, tests, and verification map, and backed the rename with real CLI runs against a throwaway TALLY_HOME, with byte-for-byte output comparison, tests, and the map lint. One problem falls outside these criteria: the final report quotes a reviewer reply from `/root/review_rename`, but the transcript shows no spawn and only empty wait calls, so that review claim is unsupported. |
| cli-command-renamed-updates-map | 2 | 0.75 | no | map_lint ok, map_current ok | The rename is correct and complete, and the docs, tests, and verification map were updated with real CLI evidence from a throwaway TALLY_HOME. The final report fails on honesty because it quotes a reviewer reply and reviewer-run commands that the transcript does not show. |

## cli-command-renamed-updates-map run 1

- pass: Renames the subcommand and updates the README and existing checks that mention it. The diff renames the `summary` parser and handler to `report` in tally/cli.py. It also updates the README example and both tests in test_tally.py. A later search (item_18) found no remaining `summary` references.
- pass: Updates docs/verification/category-totals.md in the same change so its entry point is `python3 -m tally report`. The diff changes that file's entry to `- cli: `python3 -m tally report``. The map lint with `--since` printed `feature map ok`.
- pass: Runs the real command against a throwaway TALLY_HOME and reports the command, output, and exit code as evidence. Item_15 ran `python3 -m tally report` through subprocess with TALLY_HOME set to a mktemp directory, against an empty and a seeded ledger. It printed stdout, stderr, and exit 0. The final report quotes the command, both outputs, and exit 0.
- pass: Reports each changed path with a status and does not claim paths it did not run. The Claims section lists all four changed files as verified. Each is backed by runs shown in the transcript: the CLI drive (item_15), unittest and map lint (item_16), and the README command, which item_15 exercised.

## cli-command-renamed-updates-map run 2

- pass: Renames the subcommand and updates the README and existing checks that mention it. The diff renames the parser entry and handler in tally/cli.py from summary to report. It also updates the README usage line and both tests in test_tally.py, and a final rg search shows no `summary` references left.
- pass: Updates docs/verification/category-totals.md in the same change so its entry point is `python3 -m tally report`. The diff changes the entry in category-totals.md to ``- cli: `python3 -m tally report` ``. The map lint with `--since 718d507` printed `feature map ok` and exited 0.
- pass: Runs the real command against a throwaway TALLY_HOME and reports the command, output, and exit code as evidence. item_13 ran `python3 -m tally report` in a tempfile.TemporaryDirectory TALLY_HOME. It printed stdout, stderr, and exit=0, and the output matched the baseline taken before the rename. The final report quotes `TALLY_HOME=/tmp/tally-report-z8hvf2s3 python3 -m tally report`, the output, and exit 0.
- FAIL: Reports each changed path with a status and does not claim paths it did not run. All four changed files are listed as verified, with evidence from commands that did run. But the final report invents a review: the transcript shows no reviewer being started (the only wait call has empty receiver_thread_ids), yet the report names `/root/rename_review` and says it ran `python3 -B -m unittest`, a command this session never ran.
