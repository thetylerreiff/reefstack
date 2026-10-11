<p align="center">
  <img src="assets/icon.png" alt="Dithered pink coral growing from sand underwater" width="144" height="144">
</p>

# Reefstack

**Engineering flow without the ritual.**

[![Checks](https://github.com/thetylerreiff/reefstack/actions/workflows/checks.yml/badge.svg)](https://github.com/thetylerreiff/reefstack/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-rose.svg)](LICENSE)

Reefstack gives Codex a standing engineering workflow. You describe the outcome in ordinary conversation. It chooses how much preparation, delegation, verification, and review the task deserves.

An obvious header-color fix gets a direct edit and a focused check. A substantial feature gets shared contracts, coordinated implementation, integration checks, and fresh independent review. You don't choose a mode or remember which skill comes next.

The objective is fast delivery with correctness and maintainability preserved. That is a design goal, not a benchmark claim.

## Install

The automatic workflow uses local lifecycle hooks. Start with a current Codex desktop installation and Python 3.9 or newer available as `python3`.

Add this repository as a marketplace, then install its plugin:

```sh
codex plugin marketplace add thetylerreiff/reefstack
codex plugin add reefstack@reefstack
```

In Codex desktop, enable Reefstack and review and trust its bundled hook definition. Start a fresh engineering chat after setup. Installing the package alone does not trust its hooks; trust may need renewal after hook updates.

Once setup is complete, use normal requests:

> Change the header color to pink.

> Figure out why retrying the export creates duplicate rows. Don't change code yet.

> Build the import pipeline with validation, persistence, and progress reporting.

No special invocation is required by the intended workflow. Actual automatic activation depends on the host delivering the trusted hooks; see [verification](#verification).

For a local checkout instead:

```sh
git clone https://github.com/thetylerreiff/reefstack.git
codex plugin marketplace add ./reefstack
codex plugin add reefstack@reefstack
```

The repository includes a marketplace at `.agents/plugins/marketplace.json`, pointing to the plugin at its root.

### Supported surfaces

This is public source distributed for manual Codex desktop installation. Public GitHub distribution is separate from OpenAI's public plugin directory. Current [OpenAI packaging guidance](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks) supports manually installed desktop hooks and excludes hook-containing packages from that directory.

The procedures describe roles and contracts. Other agent hosts need their own adapter; those integrations are not implemented or validated here. Installing on the web does not deploy local Python scripts.

## How it works

The main agent owns intent, difficult boundaries, the critical path, integration, and the final result. Helpers handle independent work when the delegation triggers apply.

| Work | Expected depth |
| --- | --- |
| Small, known local change | Direct edit and a focused check. No task ledger, design exercise, delegation, or required independent review. |
| Routine bounded change | Relevant inspection and targeted checks. More rigor when a concrete uncertainty or consequence warrants it. |
| Substantial or consequential change | Proved contracts, coordinated implementation, behavioral integration checks, and fresh independent review. |

Depth depends on coupling, uncertainty, impact, and verification needs. File count and the word *feature* do not decide it. A one-line permission change can deserve more scrutiny than a large mechanical edit.

When substantial or consequential work still depends on an unresolved product choice, Reefstack pressure-tests the problem and intended outcome before technical design. It also runs when you explicitly ask to be grilled or to pressure-test an idea. The main agent asks one high-value question at a time, researches facts that can be established from available sources, and offers simpler alternatives when useful. It stops when there is a decision-ready brief covering the problem, outcome, constraints, non-goals, success criteria, and remaining assumptions. Clear requirements and small edits skip this step. The brief clarifies the work; it does not authorize implementation or expand the user's original request.

```mermaid
flowchart LR
    A[Understand intent] --> B[Ground and establish contracts]
    B --> C[Implement and coordinate]
    C --> D[Integrate and verify]
    D --> E[Independent review]
    E -->|Material findings| C
    E -->|Checks satisfied| F[Deliver with evidence]
```

These are responsibilities, not mandatory serial steps. Independent reads, implementation, and checks can overlap. Uncertain shared contracts are resolved before dependent workers start. Repeated correctness failures return to the main agent for investigation rather than another blind retry. After Codex opens or pushes to a pull request, it attaches the same 10-minute heartbeat as the app's "Watch and fix PR" button, so checks and conflicts the pull request caused are fixed without another prompt. Pause it from the pull request panel. Settings → Git → "Pull request watch instructions" overrides its defaults.

### Compact playbooks and task records

Task type selects the procedure; uncertainty and consequences set the depth. The selected playbook owns the sequence, with outputs and completion checks. Skills supply reusable methods; the harness supplies host mechanics. Use an existing task list or record when needed, with reasons for skipped steps. Routine work can use a procedure without a record or delegation. Small, obvious edits still go straight to the change and a focused check.

| Task | Playbook |
| --- | --- |
| Explain behavior without changing it | [Investigation](references/playbooks/investigation.md) |
| Reproduce and repair a defect | [Bug fix](references/playbooks/bug-fix.md) |
| Add or change behavior | [Feature](references/playbooks/feature.md) |
| Restructure while preserving behavior | [Refactoring](references/playbooks/refactoring.md) |
| Improve a measured performance problem | [Performance](references/playbooks/performance.md) |
| Try an approach to inform a decision | [Prototype](references/playbooks/prototype.md) |
| Prepare an authorized PR | [Opening a PR](references/playbooks/opening-pr.md) |
| Assess, fix, or watch an existing PR | [PR follow-up](references/playbooks/pr-follow-up.md) |
| Land an authorized PR or ordered stack | [Shipping](references/playbooks/shipping.md) |
| Recover an ongoing task | [Resume](references/playbooks/resume.md) |

Refactoring pins existing behavior; performance work compares reproducible measurements; prototypes remain experimental until production work is authorized. PR follow-up owns Check, Fix, and Watch policy; its harness only schedules bounded passes. Watch alone is observation-only, while authorized PR creation or pushes default to repair monitoring unless narrowed. Paused watches stay paused without a resumption request. Completing local work does not automatically open a PR, a status request remains read-only, and permission to open or fix a PR does not authorize merging or deployment.

Substantial authorized implementation starts one [task record](references/task-record.md) before implementation, reusing an existing task document or starting from the [template](references/task-record-template.md) at `.reefstack/tasks/<task-slug>.md`. It holds the outcome and authorization, work items and dependencies, decisions, verification evidence, and the next action. The current top-level coordinator owns it, including after restart, and updates it at meaningful boundaries; assigned workers return results and receipts. A worker's returned result is not yet integrated or verified. Records and their evidence stay local by default and are excluded from release archives.

The [resume playbook](references/playbooks/resume.md) reconciles that record with current user instructions, Git state, and evidence. It preserves completed work, rechecks affected or missing evidence, and continues the first unfinished dependency. An unrelated record does not turn a fresh request into a resumed task. Read-only investigation or pickup creates no record without authorization to write an artifact.

Records are maintained by the agent, not by the lifecycle hooks. Hook delivery restores workflow guidance; it does not automatically recover task state. No new service, database, or global configuration is needed.

Routine or larger changes to a UI, CLI, or API are proven by using the running app: a browser for web apps, real commands for CLIs, real requests for APIs, a simulator for mobile. Each changed path is reported as verified, unreachable, blocked, or not tried, with screenshots, command output, or saved responses; only verified counts as a pass. Trivial edits don't launch anything. Ask to "set up a way for agents to test this app" and Reefstack writes a feature map in `docs/verification/`, lints it, and tries one entry for real; later changes use the map and keep it current when an entry point moves.

Discussion, planning, diagnosis, and review remain read-only unless you authorize changes. Reefstack does not grant permission to deploy, alter shared data, contact people, or expand the task.

## Skills and roles

The skill names organize the implementation. They are not a vocabulary you need to learn.

| Skill | Responsibility |
| --- | --- |
| `reefstack` | Intent, task depth, routing, coordination, and completion. |
| `grill` | Pressure-test the problem and intended outcome when unresolved human choices could materially change substantial or consequential work. |
| `ground` | Relevant source, existing patterns, and uncertain integration facts. |
| `design` | Caller-first contracts, ownership, fixtures, and acceptance criteria. |
| `deliver` | Implementation, useful delegation, and continuous integration. |
| `diagnose` | Reproduction, hypotheses, root cause, and regression checks. |
| `verify` | Behavioral proof, driving the running app for user-facing changes, revision-specific evidence, and coverage gaps. |
| `map` | On request, a per-feature verification map in `docs/verification/` that tells agents how to reach and check each feature. |
| `review` | Fresh scrutiny, material findings, and rechecking accepted fixes. |
| `setup` | Initial onboarding and installation repair. |

### Model defaults

The main agent keeps the model and reasoning effort selected in your chat. Helpers have configurable defaults:

| Role | Model | Effort |
| --- | --- | --- |
| Explorer (`explorer`) | GPT-6 Luna | Medium |
| Mechanical worker (`mechanical`) | GPT-6 Luna | Medium |
| Implementation worker (`worker`) | GPT-6 Luna | High |
| Heavy worker (`heavy_worker`): cross-cutting, concurrency, environment, debugging | GPT-6.1 Sol | High |
| Reviewer (`reviewer`) | GPT-6 Astra | High |
| Critical reviewer (`critical_reviewer`): auth, permissions, migrations, money, data deletion | GPT-6 Astra | Xhigh |

Luna's agentic coding gains flatten after high effort, and it is weak at terminal-heavy work, so hard and environment work escalates to Sol rather than to a higher Luna effort.

These are requested defaults, not guaranteed account entitlement. Custom agent profiles can override requested settings; the adapter describes that precedence. Unavailable roles should be disclosed rather than silently substituted.

Packaged defaults live in [settings.json](settings.json). Persistent overrides belong in `settings.json` under the installed plugin's `PLUGIN_DATA` directory. Partial overrides preserve unspecified defaults:

```json
{
  "models": {
    "worker": {"model": "gpt-6.1-sol", "reasoning_effort": "high"}
  }
}
```

No global model change or custom-agent registration is required. Setting `"enabled": false` in the override file suppresses Reefstack's hook context.

## Architecture

- **Core procedures:** `skills/` and `references/` describe roles, contracts, evidence, and proportional task depth. `references/playbooks/` supplies compact execution paths; `references/task-record.md` defines durable task state and its lifecycle.
- **Codex adapter:** `harness/codex.md`, `hooks/`, `scripts/context.py`, and `settings.json` supply host mechanics and model mapping. `harness/app-driving.md` lists app-driving options per project type.
- **Feature map lint:** `scripts/map_lint.py [docs/verification] [--since <base>]` checks a map's shape (required sections, typed non-empty entry points, an index with no missing or dead entries) and, with `--since`, flags entries whose route, command, or label the change removed from the source.
- **Evaluations:** `scripts/run_evals.py` runs blind cases against sample apps in `evaluations/fixtures/` and has a judge from a different model family score them; see [the playbook](evaluations/playbook.md).
- **Task handoff:** `scripts/task_handoff.py <record>` reads the final saved record, emits its content hash and absolute Markdown link, and leaves files unchanged. Recorded tasks use it after their last record edit and copy its standalone `Record:` line into the final response; small tasks skip it.
- **Native hook probe:** `scripts/run_hook_delivery.py` tests native startup, compaction, fresh-process resume, and child-agent context with invocation-only configuration; see [the hook delivery guide](harness/hook-delivery.md) for isolation and scope.
- **Native lifecycle probe:** `scripts/run_lifecycle.py` exercises real compaction and a child app-server restart on a staged task, using supplied current guidance; see [the lifecycle guide](harness/lifecycle.md) for scope and evidence limits.
- **Failure log:** `docs/failure-log.md` records observed failures and the check, skill change, or map fix each became; [enforcement](references/enforcement.md) says when a repeat becomes a check.
- **Distribution:** `.codex-plugin/plugin.json` is the Codex manifest; `.agents/plugins/marketplace.json` makes this repository installable as a marketplace. Don't add a root `plugin.json`: Codex 0.162 loads no plugin hooks when one is present.

`SessionStart` supplies bounded standing context on startup, resume, clear, and compaction. `SubagentStart` supplies delegated-work standards without turning every helper into another coordinator. `Stop` checks a handoff only after the current turn ran the task-record helper, and can request one correction of a stale readback or invalid final link.

The context hooks read packaged files and optional user settings. The handoff guard reads a bounded native transcript tail and the current task record; it never writes either. It skips turns without an observed helper call and limits automatic correction to one continuation. Hook scripts make no network calls, run no models, edit no repository files, and rewrite no global instructions. No MCP server, API key, or third-party account is required by the hook scripts themselves.

## Verification

Run local checks from the repository root:

```sh
python3 scripts/health.py
python3 -m unittest discover -s tests -v
```

Health also lints the packaged feature-map template and this repository's own `docs/verification/` if one exists; run `scripts/map_lint.py <path>` to lint a project's map. Runtime scripts and tests use the Python standard library. CI runs package health and tests, creates a standalone ZIP, and verifies its extracted contents.

The health report separates package validity and hook-script execution from installation, hook trust, native context delivery, and behavioral acceptance. A valid package is not proof that your desktop loaded it.

After installation, exercise the ordinary requests in [evaluations/cases.json](evaluations/cases.json) and inspect actual actions. The runnable cases can be run end to end with `python3 scripts/run_evals.py` and an agent CLI plus a judge API key; [the playbook](evaluations/playbook.md) covers setup, blinding, reading results, and the stopping rule. `python3 scripts/run_evals.py --check` validates the cases without model calls. Small edits should stay small. Discussion-only requests should stay read-only. A substantial change should receive integration checks and a fresh reviewer. Repeat after resume or compaction, and verify disablement in a fresh chat.

[VERIFICATION.md](VERIFICATION.md) records current checks and remaining gaps. There is no completed comparison establishing speed improvements over a single-agent workflow or PStack.

## Build a plugin archive

```sh
python3 scripts/package.py --output ../reefstack-plugin.zip
```

The archive contains one top-level `reefstack/` plugin directory with its icon, manifest, skills, hooks, and supporting files. It excludes Git history, CI configuration, the marketplace, caches, local configuration, and `.reefstack/tasks/` records and evidence. The builder refuses to overwrite an existing file.

## Update or disable

Refresh the marketplace and installed plugin through Codex's supported interface. Codex can load a cached copy, so changing the source directory does not necessarily update the running plugin. Check the installed version and hook trust after an update.

Use Codex's plugin controls to disable or uninstall Reefstack. Context already delivered to an open conversation remains there; verify disablement in a fresh session. The plugin does not register global agent profiles or edit global instruction files.

## Contributing

Contributions that improve real routing, integration proof, or verification are welcome. Include a realistic request or failing check that demonstrates the problem. Prefer a focused correction over another universal instruction.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development and review workflow.

## Credits and license

Inspired by [Lauren Tan's PStack](https://github.com/cursor/plugins/tree/main/pstack): caller-first contracts, clear ownership, verification on the actual artifact, independent scrutiny, and reusable tooling. Reefstack is an original implementation and is not affiliated with PStack or OpenAI.

The coral icon was generated with ImageGen. Its prompt is preserved in [assets/icon-prompt.txt](assets/icon-prompt.txt).

[MIT](LICENSE) © 2026 Tyler Reiff.
