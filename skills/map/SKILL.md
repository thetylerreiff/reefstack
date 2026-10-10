---
name: map
description: Create or refresh docs/verification/, a feature map telling agents how to reach and check each user-facing feature of an app. Use only when the user asks for it, such as "set up a way for agents to test this app" or "update the verification map"; ordinary feature work does not create a map.
---

# Map

Build the project's feature map: `docs/verification/README.md` plus one short file per user-facing feature. [Verify](../verify/SKILL.md) reads it later to know where each feature lives, what data it needs, and what success looks like. Write for an agent reading it cold, mid-task.

## Learn the app from the repository

Answer from the source and docs; ask the user only what cannot be observed.

- **Surfaces:** web UI, CLI or TUI, API, mobile, desktop. A repository can have several.
- **Launch:** the documented dev command, ports, environment variables, seed data, test accounts, and a readiness signal.
- **Drive:** existing end-to-end suites first, then the generic options in [app driving](../../harness/app-driving.md).
- **Features:** start with the three to five most used, found in routes, command definitions, API handlers, menus, or the README. More can come later.

If the app does not start as checked out, report exactly why before writing launch steps. Change product code only if the user authorized it.

## Write the map

Follow [the feature map template](../../references/feature-map-template.md). The index holds the shared launch, readiness, seed, driver, and cleanup steps and links every feature file. Each feature file covers what it is, how to reach it (every entry point, typed `web`, `cli`, `api`, `mobile`, `desktop`, or `other`, with the real handle), setup or test data, the key paths, and what success looks like. Keep implementation details out; name user paths and observable results.

Run the [map lint](../../scripts/map_lint.py) on `docs/verification` and fix every error.

## Try one entry for real

Launch the app from the index, drive one feature's key path, capture evidence, clean up, and confirm the evidence survived cleanup. Record the outcome in that feature's `## Last checked`: date, revision, entry point, status (verified, unreachable, blocked, or not tried), and the evidence location. Fix map steps the run proved wrong and run the lint again. A blocked or unreachable run still ships the map, labeled as such; never record it as verified.

## Keep it proportional

A small app with a few features is direct work with no helpers. For a large app, read-only explorers may each summarize a group of features from source; the main agent writes the map and does all the driving. The map is documentation: it does not need a reviewer unless the user asks. Report the files written, the lint result, and the entry that was tried with its status and evidence.
