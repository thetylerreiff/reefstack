# Task record template

Copy these headings into `.reefstack/tasks/<task-slug>.md`. Keep the record short and current.

## Outcome and constraints

- Outcome:
- Authorization and constraints:
- Acceptance conditions:

## Current state

- Artifact/revision and dirty state:
- Working directory, branch/base revision (or non-Git snapshot):
- Current contract revision:
- Playbook and active step:
- Live workers/processes and their owners, if any:
- Completed work with valid evidence:
- Unresolved findings or blockers:

## Work items

| Item | Owner | Dependency / contract revision | Status | Acceptance |
| --- | --- | --- | --- | --- |
|  |  |  | pending |  |

Status vocabulary: pending, in progress, returned, integrated, verified, stale, blocked, skipped. Explain skipped work. Returned means a worker supplied a result; integrated means the parent accepted it into the current artifact; verified means current evidence meets its acceptance condition. Stale work needs revalidation after a relevant change.

## Decisions

- Decision and rationale, including contract changes:

## Verification

For each receipt, include the artifact revision or content snapshot (and dirty state), command or method, observed result, evidence location, and any coverage gap. Mark evidence stale when its dependency changes.

| Path / behavior | Revision / dirty state | Method and result | Evidence | Gap / status |
| --- | --- | --- | --- | --- |
|  |  |  |  | not tried |

## Resume

- Next action and owner:
- Dependencies and unresolved blockers:
- Last updated at a meaningful transition:
