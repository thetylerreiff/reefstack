# Bug-fix playbook

Use when a defect needs reproduction or its cause is not yet established. A small, obvious correction with known behavior can stay direct. Investigation and review alone remain read-only.

1. **Pin down the failure.** Record expected and actual behavior, the affected entry point, and the narrowest case. **Output:** reproduction steps. **Check:** observe the failure or explain precisely why reproduction is unavailable.
2. **Find the mechanism.** Trace the failing path and inspect state or logs that distinguish causes. **Output:** evidence-backed cause, separating observation from inference. **Check:** the explanation accounts for the observed failure.
3. **Set the fix boundary.** Name the smallest correction, affected contracts, owner, and focused regression check. **Output:** scope and acceptance condition. **Check:** the regression check would detect the original defect; explain a skipped probe or check.
4. **Fix and integrate.** Implement only authorized scope and preserve concurrent work. **Output:** current artifact state and check result. **Check:** the changed path meets the agreed condition before dependent work proceeds.
5. **Close the evidence loop.** Re-run the original reproduction and affected checks using [Verify](../../skills/verify/SKILL.md), including maintenance and lint of an existing verification map for added or moved paths. Use [Review](../../skills/review/SKILL.md) for substantial or consequential work and recheck affected fixes. **Completion check:** current evidence demonstrates the original defect is fixed without relevant regressions. Missing proof leaves an explicit gap and next action. Local completion does not initiate PR delivery.

Use [Diagnose](../../skills/diagnose/SKILL.md) to isolate the cause and [Deliver](../../skills/deliver/SKILL.md) for coordination during implementation.
