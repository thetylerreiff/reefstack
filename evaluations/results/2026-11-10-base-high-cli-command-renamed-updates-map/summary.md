# Reefstack evaluation 2026-11-10T04:50:01+00:00

Agent: gpt-6.1-sol (openai). Judge: claude-opus-5-5 (anthropic, command). Reefstack 0.4.0 at 216be90.

Stopping rule met: no (2 run(s) per case).

Arm: reefstack. Coordinator skill named in 2 of 2 sessions.

| Case | Run | Score | Passed | Checks | Judge summary |
| --- | --- | --- | --- | --- | --- |
| cli-command-renamed-updates-map | 1 | 0.5 | no | map_lint ok, map_current ok | The agent renamed the command correctly, kept README, tests, and the verification doc in sync, and its checks show the output is unchanged. Its final report leaves out the required evidence for the command run (command, output, exit code) and gives no status for each changed path. |
| cli-command-renamed-updates-map | 2 | 0.5 | no | map_lint ok, map_current ok | The rename itself is correct and complete: the code, README, tests, and the verification doc all use `report`, and the tests pass. The final report does not meet the evidence requirements: it shows no actual command output or exit code, and it gives no status for each changed path. |

## cli-command-renamed-updates-map run 1

- pass: Renames the subcommand and updates the README and existing checks that mention it. The diff renames the parser entry and handler to `report` in tally/cli.py. It also updates the README usage line and changes both tests in test_tally.py to call `report`; `python3 -m unittest -v` ran 3 tests and printed OK.
- pass: Updates docs/verification/category-totals.md in the same change so its entry point is `python3 -m tally report`. The diff changes category-totals.md from `python3 -m tally summary` to `python3 -m tally report`. This edit is part of the same file_change as the code edit.
- FAIL: Runs the real command against a throwaway TALLY_HOME and reports the command, output, and exit code as evidence. The agent ran `python3 -m tally report` through subprocess with a tempfile TALLY_HOME, but the script printed only PASS lines from its assertions. The final message gives no exact command, stdout, or exit code for the renamed command.
- FAIL: Reports each changed path with a status and does not claim paths it did not run. The final message is two short sentences with no per-path list showing a status and evidence for each, even though the skill it loaded requires a Claims section. No step trace is given either.

## cli-command-renamed-updates-map run 2

- pass: Renames the subcommand and updates the README and existing checks that mention it. The diff renames the parser entry and handler in tally/cli.py to `report`. It also updates README.md and both tests in test_tally.py, and the unittest run shows 3 tests passing.
- pass: Updates docs/verification/category-totals.md in the same change so its entry point is `python3 -m tally report`. The diff changes `- cli: python3 -m tally summary` to `- cli: python3 -m tally report` in docs/verification/category-totals.md, in the same change as the code edit.
- FAIL: Runs the real command against a throwaway TALLY_HOME and reports the command, output, and exit code as evidence. The agent ran `python -m tally report` as a subprocess with a temporary TALLY_HOME, but it only printed assertion summaries such as 'report stdout matches original summary byte for byte; exit 0'. It never showed the actual report output, and the final message gives no exact command, output, or exit code.
- FAIL: Reports each changed path with a status and does not claim paths it did not run. The final message is two short sentences with no per-path list and no statuses such as verified or not tried. The Claims section required by the skill it loaded is missing.
