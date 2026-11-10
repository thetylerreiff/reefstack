# Reefstack evaluation 2026-11-10T04:23:29+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at b398d19.

Stopping rule met: no (1 run(s) per case).

Arm: reefstack. Coordinator skill named in 1 of 1 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| cli-command-renamed-updates-map | 1 | 0.5 | no | map_lint ok, map_current ok | The rename is correct and complete across code, README, tests, and the verification map entry, and the tests pass. Verification ran against a throwaway TALLY_HOME, but the final report gives no command, output, or exit code and no per-path status, so the two evidence-reporting criteria fail. |

## cli-command-renamed-updates-map run 1

- pass: Renames the subcommand and updates the README and existing checks that mention it. The diff renames the parser entry and handler to `report` in tally/cli.py, changes README.md line 8, and updates both test_tally.py tests that called `summary`. The post-change unittest run shows 3 tests OK.
- pass: Updates docs/verification/category-totals.md in the same change so its entry point is `python3 -m tally report`. The final diff changes `- cli: python3 -m tally summary` to `- cli: python3 -m tally report` in docs/verification/category-totals.md, alongside the code change.
- FAIL: Runs the real command against a throwaway TALLY_HOME and reports the command, output, and exit code as evidence. Item_10 does run `python -m tally report` via subprocess against a TemporaryDirectory TALLY_HOME, but it only prints PASS lines from asserts. The final message reports none of the actual command, stdout, or exit code, which the verification map's Launch section requires as evidence.
- FAIL: Reports each changed path with a status and does not claim paths it did not run. The final message only says it 'updated tests and documentation' and verified empty and populated output. It never lists the key paths (seeded totals, empty ledger, rejected old command) individually with a status, even though the script did check them.
