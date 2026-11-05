---
name: blast-radius
description: Find what a proposed or finished change could break beyond its own lines, and the one fact it is safe because of. Use when the user asks what a change could break, how far it reaches, or whether something is safe to change or remove, and to size consequential work before building it. Small known edits skip it.
---

# Blast radius

Find what a change breaks somewhere else. Listing callers is the easy part; a search does that. The job is the reach a search misses, and the one fact the change is safe because of.

Use it when the user asks, or at the planning step of consequential work when what depends on the changed code is not already known. Its result sets the depth: wide or uncertain reach makes work consequential, and contained reach keeps it routine. A small known edit, or a change the user asked to make quick, skips it. On request it is read-only and does not authorize the change. Probes use scratch copies and disposable data, never shared state.

## Steps

1. **Read the change.** For a proposal, the code it would touch; for a diff, the diff. Name what it adds, changes, and removes, and what now behaves differently that the diff does not spell out: defaults, ordering, timing, error types.
2. **Find the safety fact.** A change that looks risky is usually safe, or unsafe, because of one fact, such as "only the renderer reads this field" or "every existing row already satisfies the new constraint". Find it before listing possibilities; when it holds, most risks clear together.
3. **Look where search stops.** Check what applies:
   - data the current version already wrote: files, rows, caches, queued messages;
   - formats read elsewhere: API responses, exports, parsed logs, another language reading the same bytes;
   - names held in strings: configuration, routes, flags, environment variables, templates, reflection, documentation;
   - the dependency's own source at its pinned version, and any local patch;
   - when code runs: startup, teardown, retries, concurrency, event order;
   - consumers a few hops downstream, and deployed clients older than this revision.
4. **Weigh each risk.** Give each a real likelihood and cost, with a `file:line` or the command that showed it. A search that finds nothing is an answer; record it. Never invent a caller or an API.
5. **Prove the safety fact.** Run a script or test that calls the real code and fails if the fact is false; for persisted data, write state the way the current version does and read it with the changed code. Report how far the proof reached: asserted, cited at a line, reasoned through step by step, ran, or reproduced in the running app. Only the last two count as proven; anything less is reported as unproven.

## Report

- **Change:** what it does, including the part that is not obvious.
- **Safety fact:** the fact, its proof, and how far the proof reached, or unproven.
- **Reach:** what depends on the change, and the depth that implies.
- **Risks:** how each breaks, where, its likelihood and cost, and the check that catches it.
- **Cleared:** what was checked and why it is fine.
- **Before merging:** the cheapest check that catches the real risk, including any script written here.
