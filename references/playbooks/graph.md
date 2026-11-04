# Playbook graphs

A graph playbook is a dependency graph written as numbered steps. Each step consumes named outputs of earlier steps and produces one of its own. `scripts/playbook_lint.py` checks the shape; the rules below govern running it.

## Step fields

- **Needs:** the outputs this step consumes, from earlier steps. Step 1 may omit it.
- **Output:** the one output this step produces, named in backticks, then what it contains.
- **Check:** what must hold before a later step uses the output.
- **On fail:** where a failed check returns when the fault lies upstream: `→ step K` with the condition, one arrow per target. K is an earlier step this one depends on.
- **Repeat:** a loop that runs on success: `→ step K` back to this step or one it depends on, with the condition for another pass. Every Repeat has a Bound.
- **Bound:** what stops the loop: an earlier output naming the items or stopping condition, or a decision by the user. The agent cannot extend its own bound.
- **Completion check:** the last step's condition for the whole playbook.

A step is one numbered line; indented lines below it continue it.

**Enter at:** before the steps names a later starting step and the outputs another playbook carries in. They must still hold on the current revision.

## Running rules

1. **Inputs first.** A step runs only when its inputs are valid. A step that does not apply is skipped with a short reason; what already exists in its place, such as the current code's contract, then serves the steps that need it. Small work stays small.
2. **Invalidation.** An output holds for the inputs and revision it came from. When an output changes, everything that needs it, directly or through other steps, is stale. Recheck only the stale part.
3. **Backtrack.** A failed check returns to the step named by **On fail** and reruns what depends on it. Do not patch the symptom where it surfaced.
4. **Bounded loops.** Each pass of a Repeat is compared against the state it builds on: the original baseline whenever every pass must preserve it, otherwise the last kept state. Keep each pass's evidence beside the earlier passes'. Repeat passes are not failures. An **On fail** edge taken a second time for the same check on the same unit or pass means the premise lies further upstream: go to the earlier step that the failure implicates, or stop with a blocker.
5. **No separate state.** Progress lives in the host's task list; these graphs are documents, not records.

## Output names

| Name | Contains |
| --- | --- |
| `question` | the behavior or decision to explain, with its scope |
| `path` | the traced code path, with file pointers |
| `observation` | a probe result and the method that produced it |
| `finding` | an answer, separating verified fact from inference |
| `repro` | reproduction steps for a defect |
| `cause` | the evidence-backed mechanism of a defect |
| `fix-boundary` | the smallest correction, its scope, and its regression check |
| `acceptance` | checkable acceptance conditions and remaining work |
| `contract` | agreed contract revision, workstreams, and ownership |
| `workstream` | one workstream's work and its boundary-check result |
| `baseline` | behavior or measurements to compare against |
| `hypothesis` | a falsifiable explanation or improvement idea |
| `structure` | target structure, affected callers, and bounded units of work |
| `bounds` | experiment scope, alternatives, scratch location, and stopping condition |
| `sketch` | a runnable, labeled-disposable experiment for each alternative |
| `decision` | a supported choice with its limitations |
| `change` | the current integrated artifact state at a revision |
| `evidence` | check and exercise results tied to a revision, with gaps |
| `findings` | review findings, each accepted or rejected with a reason |
| `pr-state` | a pull request's live head, base, checks, and reviews |
