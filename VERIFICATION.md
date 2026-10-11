# Verification

This report distinguishes checks of the package from native host activation. Updated October 10, 2026.

## Package and runtime checks

The local health check and unittest suite exercise:

- Manifest and skill references, lifecycle matchers, and declared shell commands.
- Startup, resume, clear, compaction, and delegated-agent context.
- Partial model overrides and disabled output.
- Input/settings rejection and exclusion of untrusted payload text from generated context.
- Relocation and shell quoting when the package path contains spaces.
- Separation of coordinator and delegated-agent context.
- Role configuration and separation of core procedures from named host/model mechanics.
- Standalone archive layout, inclusion, exclusions, output safety, and extraction.
- Feature-map lint: required sections and order, typed non-empty entry points, index coverage, `Last checked` statuses, CLI exit codes, and health's lint of the packaged template and any `docs/verification/`.
- Map drift check (`--since`): a renamed route in the web fixture and a renamed subcommand in the CLI fixture are flagged in real git repositories, and clear once the map moves or the old name is kept as an alias.
- Evaluation runner: case and fixture validation, blinding rejection, neutral workspaces, environment scrubbing, simulated port-binding denial, cleanup of servers the agent leaves running, deterministic checks and agent exit status overriding the judge, judge-reply failures and retries, input truncation, re-judging saved sessions, the stopping rule (full suite, committed procedures, consecutive runs), the judge's request shape, key handling, and the command-line transport, all with a fake agent and a mock judge. No model was called.
- Failure log entries name an outcome and an enforcing file that exists.
- Compact playbook and task-record references, including links inside the playbooks; release archives include the procedures and template but exclude private task records and evidence.
- Actual shell-hook transport on startup, resume, clear, and compaction exposes the recovery references without reading, creating, or changing workspace task records. This checks delivery of instructions, not recovery performed by an agent.
- Workflow fixtures apply a real partial CLI change and supplied record in a Git repository. Deterministic checks reject missing records for the substantial case, unexpected records for the small case, and record/source edits for read-only pickup. A record's existence does not prove its contents are correct; that remains a behavioral criterion.
- Final task-state snapshots preserve ignored records and local evidence for judging and rejudging after the temporary project is removed, with byte limits and no symlink traversal. Binary evidence is saved but not rendered by the text judge; unavailable evidence is reported explicitly.

The icon is a square 1254-by-1254 PNG, below the documented size limit, referenced by both logo and composerIcon.

CI runs the package health check and tests and checks an extracted standalone archive. The workflow status shows its actual result; the existence of the workflow is not a passing run.

## Behavioral evidence and limits

Isolated forward-tests with supplied startup context exercised a direct visual edit, a read-only contract discussion, and a bounded parser/rendering/CLI feature. These tested guidance under supplied context, not native lifecycle delivery. They were not blinded comparisons against other workflows.

The grill scenarios in `evaluations/cases.json` specify intended positive and negative routing behavior, including vague product intent, an explicit request to pressure-test, clear substantial requirements, a tiny edit, and technical uncertainty that should be researched. They are evaluation cases, not completed test results. Those case definitions do not establish grill behavior or native automatic activation. Two isolated first-turn checks with supplied startup context observed a focused bottleneck question for an ambiguous merge-bot idea with no edits, and a direct header-color edit with no interview. They do not establish adaptive follow-up behavior or native lifecycle delivery.

No runnable case has been run against a real agent and judge yet; there are no results in `evaluations/results/`. The app-driving cases in `evaluations/cases.json` (a UI change that must be driven, a typo that must not launch the app, a sandbox-blocked launch that must be reported as blocked, a moved entry point that must update the map, and an explicit map request) are specifications, not completed runs. The lint checks a map's shape, not whether its entry points still match the app; that depends on agents following the verify procedure and on review.

Codex's `hooks/list` (0.162.0-alpha.2) returns no Reefstack hooks while a root Agent Plugins `plugin.json` exists, even with `extensions.com.openai.hooks`. With only `.codex-plugin/plugin.json`, it lists the SessionStart and SubagentStart hooks as untrusted, ready for review.

Native desktop startup/resume/compaction delivery, trust state, substantial-task automatic delegation and review, and end-to-end speed improvements remain environment-specific acceptance checks. Skill discovery alone does not prove any of those states.

The compact playbooks and durable records are agent procedures. Supplied-record continuation cases exercise recovery from a prepared project state; they do not simulate native compaction, prove durable state across a host restart, or replace a live multi-turn acceptance run. Package and fixture tests must not be described as those behavioral results.

Automated source and extracted-archive suites passed; the 29-test runner suite was rechecked after the ignored-record snapshot fix. The archive now includes the public failure log needed by its shipped tests. Isolated supplied-context probes observed a direct typo edit without a task record and a read-only pickup with no source/record edits. An initial import probe skipped the record and a resume probe left stale handoff text; the routing and closeout instructions were tightened. A fresh import probe created a record with evidence and independent review, and a fresh top-level CLI resume reconciled the record and alias requirement. The latter still failed the verification-map shape check. A delegated resume probe also left record updates to its parent. These mixed observations are not a passing behavioral suite, and delegated ownership should not be mistaken for a top-level lifecycle test. At that stage, no native compaction or restart recovery had been exercised; the later native probe below covers those transitions.


## Workflow follow-up: native lifecycle evidence

On October 10, 2026, a three-turn Tally task ran on `gpt-6-luna` at high effort through a real Codex app-server compaction and process restart. The probe observed a completed `contextCompaction` item and its matching successful turn, continued with a newer alias requirement, stopped its own server, then resumed the same persistent thread in a fresh server. The resumed agent read the on-disk record and Git state. Independent checks passed for populated-ledger totals, `report`/`summary` parity, the unit suite, map shape, and map drift.

The initial handoff had a stale “in progress” work-item row despite passing checks. After compaction it reconciled the row, and after restart the final Current state, Work items, Verification, and Resume agreed with the artifact and latest alias requirement. This is evidence of recovery from inconsistent bookkeeping, not a guarantee that intermediate records never drift. The resumed agent also initially wrote an invalid map entry, ran the now-visible linter, corrected the entry, and reran successfully before handoff.

The repeatable command and coverage are in [the lifecycle guide](harness/lifecycle.md). This test supplies current repository guidance as developer instructions and excludes installed plugins per turn; it does not install or trust hooks and does not prove native hook delivery or desktop-app restart behavior. An earlier attempt read an older installed Reefstack copy and is retained as mixed-host evidence, not credited as validation of the current procedures. Persistent native thread identity, protocol events, record snapshots, and artifact checks are retained locally under `.reefstack/tasks/compact-workflows-evidence/`.

Fresh import-task replays exposed both missing record creation and missing map coverage, even after the agent read the surrounding guidance. A valid old map passed shape lint while omitting the new command. The import fixture now explicitly rejects missing command coverage, and the compact playbook itself makes on-disk record creation, map maintenance/lint, and record readback concrete stage outputs. These trial failures remain in the local evidence; they must not be erased by a later passing run. The separate typo replay remained a direct edit with no task record.

The final fresh import replay created its task record before product edits, updated the existing map, and passed all three deterministic checks (`task_record`, `import_map_entry`, `map_lint`). Seven app unit tests and actual CLI checks passed; independent inspection found the final record reconciled. The handoff still omitted its record link and a final record readback, and receipts mostly referenced session output. These are remaining process misses, so this is a targeted acceptance result, not full playbook compliance or a blinded-suite pass.

The updated source suite exercised 95 tests; two failure-log schema assertions exposed invalid outcome labels, which were corrected and rechecked. All 95 tests passed from the extracted standalone archive. These include failed/partial compaction, wrong thread/turn events, timeout/EOF, process-group cleanup, per-turn plugin isolation, and replay of the map defects. No model call is part of the unit suite; the native run is separate live evidence.

## Record handoff and native hook follow-up

The read-only `task_handoff.py` helper returns the final saved record, its hash, and an absolute Markdown link, with a standalone `Record:` line for the final response. The Codex JSONL handoff check requires a successful helper call matching the final bytes and the exact link in the last assistant message. It rejects missing or stale readbacks, failed calls, unrelated records, and mistyped links. This verifies readback transport and file identity, not semantic truth or universal agent compliance.

The initial 110-test source suite passed. Fresh independent review found that the native evidence directory inherited overly broad permissions; it now uses owner-only mode with a regression test. A supplied-record resume replay passed map shape, map drift, and the handoff check after the helper made the link a standalone copyable line. A separate small typo replay still created no record. Three substantial-task replays read their records correctly but mistyped a character in their long temporary-directory links; the check rejected those handoffs. One import replay noticed stale Resume wording during readback, corrected it, and reran the helper. Failed trials remain evidence and do not count as full workflow passes.

The native `Stop` guard now checks an observed helper call in the current thread and turn against the saved record and final response. It requests at most one correction, performs no writes, and stays quiet on turns without a helper call. An explicit `--no-guard` preserves user requests for incompatible output formats. Missing/unsupported transcripts, helper calls outside the supported command forms, and alternate record locations remain coverage gaps; the guard does not prove semantic record quality or detect every omitted helper invocation.

The opt-in [native hook probe](harness/hook-delivery.md) exercised actual SessionStart startup/compact/resume and SubagentStart events on Codex CLI 0.160.0. It packages the current source, runs its adapter through native command hooks with invocation-only exact-definition trust, and appends a fresh token only in hook output. Native event identities plus exact model replies establish delivery; the untrusted control returns no token and executes no hook. Resume uses the same persisted thread in a new owned app-server process. The tests reject tool/file-read shortcuts and isolate ambient hooks.

Initial native runs passed all four delivery paths with unchanged saved settings. A repeat also passed delivery but failed the configuration guard while a concurrent CLI behavior trial saved trust for its temporary project. Inspection found only those probe-project entries, not saved trust for the native test hooks. The four entries from this follow-up were removed without changing other settings. The subsequent serial native run passed all four paths and the unchanged-configuration guard. Native checks must run separately from those CLI trials; ephemeral CLI sessions are not a configuration-isolation guarantee.

A final native run on Codex CLI 0.160.0 passed startup, post-compaction delivery, same-thread resume in a fresh app-server process, and child delivery again, then deliberately omitted the record link. The real Stop hook blocked that handoff; the agent invoked the helper a second time and returned its exact record link. The two readbacks matched the unchanged fixture, and saved configuration hashes remained unchanged. The source archive hash was `0c62b4bcb4afa05a248ae15e3f6442e71a64b9b7c633e9b131f4625d181ad70b`; native events, hook inputs/outputs, and result are retained locally in `.reefstack/tasks/compact-workflows-evidence/native-hooks-final/`. This targeted correction trial is distinct from a fresh end-to-end import-task acceptance run.

All 139 source tests passed with local socket binding available; the sandbox-only attempt failed that environment-dependent socket test. The review fix makes explicit opt-outs and alternate canonical record locations remain uncovered without reading outside the default directory or demanding a replacement. The final guard and hook evidence tests passed (25 and 10 tests). Saved native Stop inputs and events were replayed against the final code: the initial miss still blocks, the corrected link passes, and separate native blocked/completed events are required. This replay reuses the valid live evidence; it is not a new model run.

This is native invocation-configured delivery through an instrumented source snapshot. Local selected-root discovery produced no events in a bounded test and remains unverified. Plugin installation, trust onboarding, desktop delivery, and native clear delivery are not established by these runs. The full blinded agent-and-judge suite was not run.

## Expanded compact playbooks

Refactoring, Performance, Prototype, Opening a PR, PR follow-up, and Shipping now have dedicated compact procedures. Source health and all 141 unit tests passed, including package-reference checks for each added playbook and the existing PR-watch dependency. The extracted package passed health validation. A fresh model routing dry run selected the expected route for 14 held-out requests; parent inspection checked the proposed evidence and authorization boundaries, including read-only PR status, stale review, blocked stack order, and changed performance data after restart.

This is routing evidence, not execution of the hypothetical tasks. No actual PR was opened or merged, watch started, performance benchmark run, or prototype built for these trials. Existing native-hook evidence concerns unchanged adapters and does not establish compliance with the added playbooks. The full blinded behavioral suite was not run for this expansion.

## Playbook consolidation

The selected playbook now owns workflow order; the coordinator routes by task type and scales effort separately. PR follow-up owns Check, Fix, and Watch policy, with the host harness limited to scheduling and transport. Shared task-record readback remains the canonical closeout contract. Routine procedures do not inherently require records or helpers.

All 150 unit tests passed on local Python 3.9 and 3.13, and source health plus evaluation-case validation passed. The suite includes eight held-out CLI contract checks and three new runnable scenarios for a behavior-preserving refactor, measured optimization, and disposable prototype. The local Python 3.10/Linux CI leg was not run. These unit checks establish fixture behavior and packaging, not agent adherence.

Fresh task agents supplied with current working-tree guidance completed local fixture work. The returned refactor and optimization each passed all eight parent-run held-out CLI checks. The refactor agent ran the original three CLI tests before editing; its additional boundary matrix was temporary, so the retained checks provide stronger reproducible evidence than that session-only receipt. The optimization passed a separate parent-run alternating comparison of the original and final real CLI, with identical input/output bytes on representative and small workloads, plus the original project tests. These are fixture-specific timings, not Reefstack speed claims.

Independent review found that the optimization trial changed error precedence when both an order and a customer row were malformed, despite the original eight checks passing. The added case reproduced the failure; the isolated trial artifact was corrected, the affected checks passed on both original and returned artifacts, and the real-CLI comparison was refreshed. The complete 150-test runs preceded this test extension; the affected eight-test suite was rerun on Python 3.9 and 3.13 afterward. The trial's earlier handoff is historical evidence, superseded by the parent's post-review receipts.

The disposable prototype stayed under its scratch directory, with production source, tests, and README byte-identical. Both interfaces were exercised in a real browser for selecting and removing parcels. Directed follow-up checks confirmed empty selections and nonexistent-customer searches. A separate tiny-edit trial changed only the requested word, without a record. Three instrumented local PR passes preserved a paused status-only watch, left a pending observation watch unchanged, and paused a closed PR's until-merge watch. The simulated adapter's status read initially ignored a saved pause; it was corrected and the persisted pause was reread. No real PR, scheduler, or merge was exercised.

These are targeted source-guided trials with parent acceptance checks, not the full blinded agent-and-judge suite or proof of default native activation. Native hook delivery, plugin discovery, installation, and trust were not retested; prior delivery evidence does not establish adherence to these revised procedures. Local receipts and retained artifact paths are recorded in `.reefstack/tasks/playbook-consolidation.md` and its evidence directory.

## Acceptance in a host

Install and enable Reefstack through the supported interface, review and trust its hook definition, and start a fresh engineering chat. Exercise evaluations/cases.json, including both the grill and skip cases, and inspect actual questions, research, actions, artifacts, and reviewer activity.

Include a substantial multi-component task, a small local edit, a planning-only request, a failed-worker correction, and unavailable-model handling. Check resume, compaction, and disablement in a fresh session. Record the client version, actual models, code state, checks, elapsed time, corrective rounds, and any escaped defects.

A skipped runtime check is not a pass. Package validity, installation, enablement, trust, context delivery, and verified behavior are separate results.
