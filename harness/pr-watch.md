# Watching a pull request in Codex

[PR follow-up](../references/playbooks/pr-follow-up.md) owns mode, repair scope, retry limits, and stopping policy. Read it before scheduling or executing a watch. This harness only supplies Codex transport. Do not start a watch when that policy or current user instructions say to remain read-only or local.

1. Inspect `$CODEX_HOME/automations/*/automation.toml` for this PR's URL. Reuse the existing watch; leave a paused one paused unless resumption is explicitly requested. Update only when authorized and preserve the user's current scope.
2. Otherwise use `automation_update` with `mode: "create"`, `kind: "heartbeat"`, `destination: "thread"`, `name: "Auto-fix PR #<number>"` for repair watches or `"Watch PR #<number>"` for observation only, `rrule: "FREQ=MINUTELY;INTERVAL=10"`, and `status: "ACTIVE"`. Fill the prompt below. Keep its header lines exactly as written; the app matches watches by them. Copy the complete current PR follow-up playbook into the policy placeholder, so later turns retain the policy even if the package moves. Do not leave unresolved placeholders.
3. Carry the authorized mode and any narrower user instructions into the prompt. For repair watches use the execution sentence `This is a heartbeat turn. Continue automatically fixing this pull request.` For observation-only watches use `This is a heartbeat turn. Check this pull request without changing code or remote state.` Keep notification preferences in automation settings rather than the prompt.
4. Report successful scheduling or the exact limitation. Future turns read live state with `gh` or the available forge interface. Execute one policy pass, then use `automation_update` on this watch's ID to apply the playbook's pause decision. If the scheduler is unavailable, report that monitoring is not active; do not substitute a sleeping turn.

```text
## Pull request fix automation:
Repository: <owner/repo>
Pull request: #<number>
Pull request URL: <url>
Branch: <head> -> <base>

<execution sentence for the authorized mode>
Authorized mode and scope: <Watch with Fix, or observation-only Watch; specific limits>
User instructions: <current instructions, including any until-merge request>

Apply the following policy within the scope above. User instructions govern; this policy grants no additional authority. Stay quiet when state is unchanged or non-actionable; report meaningful changes, completion, failures, or needed user action.

<complete current contents of references/playbooks/pr-follow-up.md>
```
