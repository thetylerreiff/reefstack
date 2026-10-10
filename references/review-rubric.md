# Independent review

Review the stated intent and actual current diff with relevant surrounding source and acceptance criteria. Take the intent as given and challenge the execution. Avoid an implementer's persuasive narrative. Use the repository's established review conventions. An empty review is a valid result.

Assess only relevant risks:

- Observable correctness, edge cases, error semantics, and behavior regressions.
- Shared contracts across collectors, parsers, persistence, APIs, renderers, and callers. Check casing, units, missing values, and variant shapes where applicable.
- Concurrency, ownership, cancellation, retries, and idempotency when the change touches them.
- Authentication, authorization, unsafe inputs, and secret handling when applicable.
- Maintainability: architectural fit, unnecessary layers, hidden state, and duplicate sources of truth.
- Verification gaps: exercise the complete behavioral path, not only compilation or worker summaries.

Report each finding as:

```
[P1|P2|P3] short title
Location: file:line
Finding: what is wrong
Evidence: the executable path or caller that triggers it
```

Trace each finding to a real caller or input; a hypothetical case with no caller is not a finding. Do not turn speculative possibilities or personal style preferences into blockers. Preserve a proved single-reviewer finding; consensus is corroboration, not proof.

The coordinator filters rather than forwards: sort findings into fix, consider, and dismissed, each with a one-line reason, and keep the dismissed list visible. More than five fixes usually means the filter is too loose. Fix accepted findings, rerun affected checks, and recheck the relevant changes. Findings and verification belong to a particular revision; material later edits invalidate the affected verdict. Do not repeat an unchanged full review unless the fix exposes a wider issue.
