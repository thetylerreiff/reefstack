# Resume playbook

Use to continue interrupted work, or to take over someone else's branch, PR, or agent thread. The current user's instructions are authoritative and may supersede earlier plans. Read-only pickup changes no files.

1. **Rebuild the state.** Read the thread, any plan or handoff note the user points to, the branch, dirty files, and the PR if there is one. **Output:** what was asked, what changed since, and what is claimed done. **Check:** the state comes from current files and Git, not from memory or a note alone.
2. **Reconcile.** Compare the current request with the earlier plan; newer instructions win. Treat the handoff as context, not proof: a claimed pass is unverified until rechecked on the current code. Preserve other people's work and credit. **Output:** valid completed work, pending work, and conflicting claims. **Check:** no stale pass is inherited.
3. **Recheck what the next step depends on.** Rerun only the checks the remaining work relies on, within current authorization. **Output:** current results and gaps. **Check:** a read-only request edits nothing to make a check pass.
4. **Continue with the matching playbook.** Resume the remaining steps of the task's playbook. For a status-only request, report the next action without doing it. **Completion check:** unfinished work has a current gap and next action.

See [verification evidence](../verification.md) for evidence standards.
