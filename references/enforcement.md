# Turning repeated mistakes into checks

A rule an agent can skip will be skipped eventually. When the same mistake shows up twice, make the next occurrence fail on its own instead of adding another instruction.

## When it applies

- The same review finding appears in two reviews, or twice in one review.
- The same check fails twice for the same cause, or the user corrects the same thing twice.
- The project's failure log already records the mistake once.

One occurrence is a fix and a log entry, not a new check. Judgment calls that no tool can decide stay as written guidance.

## Pick the highest level that works

1. **Structure:** remove the wrong way. One owner for each piece of state, one supported path, no stale copy to imitate.
2. **Types or schema:** make the bad state impossible to write.
3. **Lint or static check:** fail with a message that names the fix, the way `scripts/health.py` in this package refuses a root `plugin.json`: it names the file that breaks hook loading and the file to use instead.
4. **Test:** a test that fails on the real past mistake and passes on the fix.
5. **Health-check entry:** a package or repository check run with the other checks.
6. **Written rule:** last, only for judgment calls.

Prove the check: run it against the original mistake (revert the fix in a scratch copy, or replay the input) and show it fails, then show it passes on the fixed code. A check that never failed has not been shown to work.

## Propose, then build

Propose the check in the review or final report: what it catches, the level chosen, why a higher level does not work, and its cost. Build it in the current change only when it is small and inside the authorized scope; otherwise hand the proposal to the user. Never weaken or skip an existing check to make room for a new one.

## Failure log

Keep a short `docs/failure-log.md` when the project has one or the user agrees to start one. Each entry is a level-3 heading naming the failure, followed by these lines:

```markdown
### Short name of the failure

- Seen: date and where (review, CI, user correction), twice if it qualified
- Cause: one sentence
- Became: skill change, check, map fix, or none yet
- Enforced by: the file, test, or rule that now catches it, or "proposed"
```

A failure whose check has caught it since needs no further rule. Delete written rules that a check has made redundant.
