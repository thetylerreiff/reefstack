# Delegation briefs

A helper starts without your conversation. Write a self-contained brief: what it needs to know, nothing it must reconstruct, and no persuasive narrative about what the answer should be.

## Explorer

One bounded question, where to start looking (paths, symbols, docs), what is already known, and the return shape: conclusions with file/line pointers, verified versus inferred, and what was not found. Several independent questions go to several explorers launched together.

## Worker

Use a short paragraph for a small independent task. For substantial assignments, include:

- Goal and observable acceptance criteria.
- Exclusive writable paths and paths owned by others. State that the worker is not alone and must preserve their edits.
- Shared interfaces, data shapes, invariants, representative fixtures, and the authoritative files that define them.
- Relevant context pointers and any upstream findings the worker cannot otherwise access.
- Required behavioral checks, known environment limitations, and what evidence to return.
- A stopping condition: report a contract problem immediately; after two failed corrections of the same acceptance condition, return evidence to the main agent.
- Report format: changes, actual checks and outcomes, deviations, unresolved problems, and artifact pointers.

Confirm that the assignment can proceed without unfinished upstream assumptions. Keep coupled implementation under one owner. When file ownership cannot be separated cleanly, serialize that work or implement it in the main agent.

## Mechanical worker

Exact scope (file list or selection rule), the transformation with one worked example, what must not change, and the check that proves every target was handled.

## Reviewer

Intent, the current diff, relevant surrounding source, acceptance criteria, and verification evidence. Point to the review rubric.

Select each helper's model and effort explicitly from the configured role defaults. Do not resume a helper merely to poll it. Reuse one when its live process or uncommitted local state makes a fresh handoff costly.
