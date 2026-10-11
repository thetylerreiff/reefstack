# Native hook delivery probe

Run this opt-in, authenticated test separately from unit checks:

```sh
python3 scripts/run_hook_delivery.py --output /private/tmp/reefstack-hooks-<fresh-name>
```

The default model is `gpt-6-luna`, effort `low`. `--model`, `--effort`, and
`--timeout` override them. The test uses tokens and creates native persisted
thread history under the existing Codex account. `--skip-subagent` omits child
coverage and records it as not requested.

The probe builds a fresh source archive and runs its actual `scripts/context.py`
through Codex's native `SessionStart` and `SubagentStart` command hooks, and
`scripts/handoff_guard.py` through `Stop`. It retains
the repository's matchers, timeouts, and context limits. A temporary wrapper
passes real native stdin to that adapter, records its output, and appends a fresh
random token. The token is absent from user prompts. The Stop wrapper passes the handoff guard’s result through unchanged. This is an instrumented
transport check, not an unmodified production-hook test.

Delivery uses invocation-only `hooks` configuration and exact-hash `hooks.state`
trust. Initial hook discovery starts no thread. The probe disables ambient hooks,
rejects enabled managed hooks that cannot be isolated, disables installed plugins
on model turns, and verifies the resulting hook states before running. It does
not install a plugin, trust hooks persistently, modify saved configuration,
override `HOME` or `CODEX_HOME`, use a trust bypass, or contact the desktop daemon.
It owns and closes each stdio app-server process. Saved `config.toml`, `hooks.json`,
and `AGENTS.md` hashes under the inherited Codex home are compared before and after; a change fails the run. Run this probe separately from CLI behavior trials: those can save temporary-project trust even with `--ephemeral` and `--ignore-user-config`. A changed hash is not attributed automatically to this probe.

A successful result requires:

- An untrusted negative control returns `NONE` and records no hook execution.
- Startup and resume hooks receive the expected native `source`, emit matched
  `hook/started` and `hook/completed` events, and deliver the new token to the model.
- Native compaction completes with its matching compaction item and turn. The
  first following turn receives a `SessionStart` event with `source=compact` and
  returns its new token. Repeating old context does not pass.
- Resume restores the same persisted thread in a new owned app-server process.
- When requested, one child receives native `SubagentStart` context, with matched
  hook events for that child's thread and turn. Native child history confirms its
  reply and the absence of tool/file reads; the parent returns that same token.
- A final handoff probe deliberately omits the first record link, requires a native Stop rejection, then requires a second readback and correct final link with no record edits.
- Ordinary visibility turns use no tools; the parent child-delivery turn allows only spawning/waiting for its child. Missing evidence, untrusted hooks,
  failed RPCs, or protocol errors fail closed.

`result.json` records runtime version, invocation, source hash, native identities,
configuration hashes, and outcomes. `source.zip`, `native-hooks.json`, wrapper,
raw native stdin/output, and redacted app-server JSONL remain under the requested
owner-only output directory (mode `0700`). Account/auth notification parameters are redacted;
other evidence can contain local paths and conversation context and is not
release content.

## Claim boundary

This proves native event dispatch, real adapter command transport, and visible
context under the scoped invocation configuration. It does **not** prove plugin
installation, marketplace discovery, trust onboarding, desktop delivery, or the
behavioral quality of the supplied instructions. `run_lifecycle.py` separately
exercises staged task continuity using supplied developer instructions; it does
not establish hook delivery.

The local CLI 0.160.0 schema also accepts `selectedCapabilityRoots`. A bounded
trial selecting a current source checkout in the local environment returned a
valid thread but no hook events. That route is unverified; accepting the request
is not evidence of plugin hook discovery. The probe therefore labels its native
configuration route explicitly.

The documented runtime boundaries are in [Hooks](https://learn.chatgpt.com/docs/hooks)
and [plugin packaging](https://developers.openai.com/plugins/build/plugins):
non-managed hooks need exact-definition trust, and plugin installation alone does
not grant it. The probe's scoped trust state is checked by `hooks/list`, not
inferred from a successful model response.
