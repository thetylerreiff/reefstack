# Delegation briefs

A helper starts without your conversation and cannot ask you questions. The brief is the contract. A field you cannot fill means the work is not scoped yet: settle it before spawning. Leave out any narrative about what the answer should be.

## Worker

For a small task, one paragraph that still names goal, scope, verify, and report. Otherwise:

```
GOAL        one sentence, the observable outcome
SCOPE       paths it may write; paths others own (it is not alone; preserve their edits)
CONTEXT     contract files, data shapes, fixtures; upstream findings pasted in full
ACCEPTANCE  checkable criteria, one per line; for any matcher or heuristic, inputs that
            must match and inputs that must not
VERIFY      exact commands, plus known environment gaps
FORBIDDEN   no edits outside scope, no shared-interface changes, no rebases or force-pushes
REPORT      changes, checks actually run with results, deviations, open problems
```

Stop and report a contract problem immediately; after two failed corrections of the same acceptance condition, return evidence instead of retrying. Keep coupled implementation under one owner; when ownership cannot be separated, serialize or do it in the main agent. A follow-up restates the full current contract, or goes to a fresh helper with it.

## Explorer

One bounded question, where to start (paths, symbols, docs), what is already known, and the return shape: conclusions with file/line pointers, verified versus inferred, and what was not found.

## Mechanical worker

Exact scope (file list or selection rule), the transformation with one worked example, what must not change, and the check that proves every target was handled.

## Reviewer

Intent, the current diff, surrounding source, acceptance criteria, and verification evidence. Point to the review rubric.

Select each helper's model and effort from the configured roles. Do not resume a helper merely to poll it.
