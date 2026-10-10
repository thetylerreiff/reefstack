# Watching a pull request in Codex

After you open a pull request or push to one, attach a watch so checks and conflicts are followed up without the user asking. This uses the same heartbeat the Codex app's "Watch and fix PR" button creates, so the pull request panel shows it as watched and the user can pause it there.

1. Skip creating one if `$CODEX_HOME/automations/*/automation.toml` already has a prompt containing this pull request's URL, active or paused. A paused watch means the user stopped it; leave it paused.
2. Otherwise call `automation_update` with `mode: "create"`, `kind: "heartbeat"`, `destination: "thread"`, `name: "Auto-fix PR #<number>"`, `rrule: "FREQ=MINUTELY;INTERVAL=10"`, and the prompt below with the placeholders filled. Keep the header lines exactly as written; the app matches watches by them.
3. Tell the user in one line that the pull request is being watched and that they can pause it from the pull request panel.

```text
## Pull request fix automation:
Repository: <owner/repo>
Pull request: #<number>
Pull request URL: <url>
Branch: <head> -> <base>

This is a heartbeat turn. Continue automatically fixing this pull request.
The following behavior is the default. Explicit custom user instructions below override conflicting defaults, but never bypass safety, permissions, or access restrictions.
Inspect the latest PR state with `gh`, including mergeability, all current checks, and new review comments.
By default, fix only failing checks caused by this PR and merge conflicts with its base branch. Do not change code for unrelated failures, infrastructure outages, or flakes; report them instead.
Start from logs and annotations before changing code. Keep changes minimal, run the focused tests for the files you change, then commit and push only to the PR branch.
Fix valid findings from automated reviewers that this PR caused, and reply on each thread with the fix commit. Summarize human review comments in this thread and ask before changing code for them.
Do not merge the pull request unless the user asks; the user controls merging.
Re-check live GitHub state instead of trusting prior turns. If checks are still pending, finish this turn without sleeping; the heartbeat will check again in 10 minutes.
When the PR is green with no actionable comments, merged, or closed, pause this heartbeat automation with the automation update tool before your final response, unless the user asked to keep watching until it merges.
If progress requires user input or unavailable credentials, ask one concise question in this thread, report the exact blocker, and pause this heartbeat automation.
Do not create or suggest another automation.
```
