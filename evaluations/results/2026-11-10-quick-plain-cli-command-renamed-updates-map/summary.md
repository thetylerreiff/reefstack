# Reefstack evaluation 2026-11-10T04:23:29+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at b398d19.

Stopping rule met: no (1 run(s) per case).

Arm: plain. Coordinator skill named in 0 of 1 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| cli-command-renamed-updates-map | 1 | 0.5 | no | map_lint ok, map_current ok | The rename itself is correct and complete: code, README, tests and the verification doc are all updated, and tests pass before and after. The agent did check the real CLI in a throwaway TALLY_HOME, but its final report gives a one-line assurance instead of the command, output and exit code for each key path. |

## cli-command-renamed-updates-map run 1

- pass: Renames the subcommand and updates the README and existing checks that mention it. The diff changes the argparse subcommand and handler in tally/cli.py from summary to report, updates the README usage line, and updates both test_tally.py tests that invoked `summary`. The post-change unittest run shows all 3 tests passing.
- pass: Updates docs/verification/category-totals.md in the same change so its entry point is `python3 -m tally report`. The final diff changes category-totals.md from `python3 -m tally summary` to `python3 -m tally report`, in the same working-tree change as the code edits.
- FAIL: Runs the real command against a throwaway TALLY_HOME and reports the command, output, and exit code as evidence. item_8 runs `python3 -m tally report` via subprocess with a TemporaryDirectory as TALLY_HOME, but it only asserts equality with the baseline and prints a 'Verified' line. Neither that run nor the final message shows the report command's stdout, stderr or exit code.
- FAIL: Reports each changed path with a status and does not claim paths it did not run. The final message makes one blanket claim of identical output for empty and populated ledgers. It gives no per-path status for the empty, seeded, help or old-command-rejection paths. The claims match what item_8 ran, but the per-path reporting is missing.
