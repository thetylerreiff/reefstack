# Independent review

Review the stated intent and actual current diff with relevant surrounding source and acceptance criteria. Take the intent as given and challenge the execution. Avoid an implementer's persuasive narrative. Use the repository's established review conventions. An empty review is a valid result.

Assess only relevant risks:

- Observable correctness, edge cases, error semantics, and behavior regressions.
- Shared contracts across collectors, parsers, persistence, APIs, renderers, and callers. Check casing, units, missing values, and variant shapes where applicable.
- Concurrency, ownership, cancellation, retries, and idempotency when the change touches them.
- Authentication, authorization, unsafe inputs, and secret handling when applicable.
- Maintainability: architectural fit, unnecessary layers, hidden state, and duplicate sources of truth.
- Verification gaps: exercise the complete behavioral path, not only compilation or worker summaries.
- User-facing changes: compare the verification report with the map and the diff, as below.

## Evidence against the map

For a change to a UI, CLI, or API, you receive the verification report and the `docs/verification/` files for the features the diff touches. Read the diff for routes, commands, flags, endpoints, and screens it adds, changes, or removes, then flag:

- **Unexercised path:** the diff changes a path, or a mapped entry point to it, with no status in the report. Report each, not a summary.
- **Verified without evidence:** a path marked verified with no screenshot, command output, or saved response, with evidence from a different entry point or an earlier revision, or with only unit tests.
- **Stale map entry:** the diff moves or renames an entry point and the map still names the old one. `python3 <package>/scripts/map_lint.py docs/verification --since <base>` catches renamed literals; read the diff for the rest.
- **Blocked counted as a pass:** a path reported blocked, unreachable, or not tried while the summary calls the change verified, done, or fully tested.

Severity follows impact: a final report that claims verification it does not have is at least P2. When no map exists, check the report against the diff alone and do not ask for a map.

## Make it a check

When a finding repeats one already in the project's failure log, or the same comment appears twice in this review, add a line proposing the check that would catch it automatically (lint rule, test, or health-check entry) per [enforcement](enforcement.md). Propose; the coordinator decides.

## Reporting

Report each finding as:

```
[P1|P2|P3] short title
Location: file:line
Finding: what is wrong
Evidence: the executable path or caller that triggers it
```

Trace each finding to a real caller or input; a hypothetical case with no caller is not a finding. Do not turn speculative possibilities or personal style preferences into blockers. Preserve a proved single-reviewer finding; consensus is corroboration, not proof.

The coordinator filters rather than forwards: sort findings into fix, consider, and dismissed, each with a one-line reason, and keep the dismissed list visible. More than five fixes usually means the filter is too loose. Fix accepted findings, rerun affected checks, and recheck the relevant changes. Findings and verification belong to a particular revision; material later edits invalidate the affected verdict. Do not repeat an unchanged full review unless the fix exposes a wider issue.
