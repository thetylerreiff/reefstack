# Investigation playbook

Use for a bounded investigation when the cause, boundary, or relevant behavior is uncertain. Small, obvious tasks do not need a playbook. Investigation is read-only; it does not authorize implementation or create a task record.

1. **Frame the question.** State the behavior or decision to explain and its scope. **Output:** one focused question and relevant boundary. **Check:** name what evidence would answer it.
2. **Trace the path.** Read the smallest set of callers, callees, configuration, and applicable procedures. **Output:** a short path with file pointers. **Check:** follow the behavior to its observable boundary.
3. **Probe uncertainty.** Choose observations that distinguish plausible explanations, within read-only authorization. Do not run a reproducer that mutates shared state. Keep credentials and private data out of evidence. **Output:** observed result and command, fixture, or method. **Check:** explain which hypothesis the observation supports or rules out, or name the unavailable boundary.
4. **Report the finding.** Separate verified facts from inference, name any unavailable boundary, and state the smallest next action. **Completion check:** the original question is answered with evidence and limitations; unresolved uncertainty is explicit.

If implementation becomes authorized, select its specific playbook through the [coordinator](../../skills/reefstack/SKILL.md); carry forward valid findings and create a task record only when the work warrants one. See [Diagnose](../../skills/diagnose/SKILL.md) and [Ground](../../skills/ground/SKILL.md).
