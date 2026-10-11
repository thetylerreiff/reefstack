# Native compaction and restart probe

Run this separately from credential-free package checks:

```sh
python3 scripts/run_lifecycle.py --output /private/tmp/reefstack-lifecycle-unique
```

The output directory must not exist. The probe uses the authenticated local
`codex app-server --listen stdio://` and the default worker model
(`gpt-6-luna`, high effort by default). Each server is a new child process with
its own process group. The probe never connects to the desktop daemon, restarts
the desktop app, installs the plugin, trusts hooks, or edits global settings.
Host permissions may require explicit approval to start that child server.
Unexpected client approval/input requests fail closed.

The model edits an isolated Tally copy in three stages:

1. Rename `summary` to `report`, create the durable record, and pause before docs.
2. After an actual completed native context-compaction item and its successful
   matching turn, amend the implementation to preserve `summary` as an alias.
3. Stop the first child server, start another, resume the same persistent thread,
   and finish the docs, verification map, and task record.

Each stage retains native JSONL protocol events (unrelated account/authentication
notifications are redacted), independent command/unit-check
results, and record snapshots. Final checks also run map lint and stale-entry
checks. `result.json` reports failure for unavailable/rejected compaction or
resume, missing native completion, timeout, or failed artifact checks. An RPC
acknowledgement alone never proves compaction. Both child servers are stopped
on completion or failure; the persisted thread and isolated workspace remain
available as evidence.

Reefstack guidance is supplied as per-thread `developerInstructions`, generated
from the current repository's `scripts/context.py`. Installed enabled plugins
are enumerated read-only and excluded on each turn using `disabledPluginIds`. Existing host configuration and global instructions
remain in effect; they are not replaced. Passing this probe proves native
compaction/resume plus the exercised behavior with supplied current guidance;
it does **not** prove current-plugin installation, hook trust, or native delivery
of that guidance. The automatic record check only verifies contract keywords
and absence of unchecked boxes; it is not a semantic handoff review. Review the
saved record snapshots and events to check semantic
handoff quality and which files the resumed agent actually read. Keep failed
runs as evidence instead of silently treating a later pass as their result.
