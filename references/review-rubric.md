# Independent review

Review the stated intent and actual current diff with relevant surrounding source and acceptance criteria. Avoid an implementer's persuasive narrative. Use the repository's established review conventions.

Assess only relevant risks:

- Observable correctness, edge cases, error semantics, and behavior regressions.
- Shared contracts across collectors, parsers, persistence, APIs, renderers, and callers. Check casing, units, missing values, and variant shapes where applicable.
- Concurrency, ownership, cancellation, retries, and idempotency when the change touches them.
- Authentication, authorization, unsafe inputs, and secret handling when applicable.
- Maintainability: architectural fit, unnecessary layers, hidden state, and duplicate sources of truth.
- Verification gaps: exercise the complete behavioral path, not only compilation or worker summaries.

Trace each material finding to an executable path and supply file/line evidence, impact, and the missing check when useful. Do not turn speculative possibilities or personal style preferences into blockers. Preserve a proved single-reviewer finding; consensus is corroboration, not proof.

The coordinator classifies findings as fix, consider, or dismiss with a reason. Fix accepted findings, rerun affected checks, and recheck the relevant changes. Findings and verification belong to a particular revision; material later edits invalidate the affected verdict. Do not repeat an unchanged full review unless the fix exposes a wider issue.
