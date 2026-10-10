# Feature map template

A feature map lives in `docs/verification/` of the project being verified: one `README.md` index plus one short file per user-facing feature. It is written for an agent reading it cold, mid-task. Copy the shapes below and replace the example app with the real one; no placeholders survive.

Rules the lint enforces (`scripts/map_lint.py` in this package):

- `README.md` has an H1, a non-empty `## Launch`, and a `## Features` list linking every feature file by file name. No unlisted files, no dead links.
- Each feature file has an H1, then `## What it is`, `## How to reach it`, `## Setup`, `## Key paths`, `## Success looks like`, in that order. `## Gotchas` and `## Last checked` are optional and come last.
- Entry points are bullets of the form ``- <kind>: `handle` `` with kind `web`, `cli`, `api`, `mobile`, `desktop`, or `other`. The handle is the real URL, command, endpoint, or screen.
- `## Last checked` has a `Status:` line with one of verified, unreachable, blocked, or not tried.
- Lowercase-hyphenated file names, at most 80 lines each.

Write from the user's point of view: entry points, stable handles (accessible names, routes, flags), required data, and observable results. Leave implementation details to the source. Record only what was actually observed in `## Last checked`, with date, revision, entry point, status, and where the evidence is. It describes one past run, not current proof.

## Index example

```markdown file=README.md
# Ledger verification map

How agents reach and check Ledger's user-facing features. Read this index, then the feature file for the change.

## Launch

- Start: `LEDGER_DATA=$(mktemp -d) make dev` serves `http://127.0.0.1:5173` and the API on port 8000.
- Ready when `curl -fsS http://127.0.0.1:8000/healthz` returns `ok`.
- Seed: `make seed` creates user `demo@example.test` (password `demo-pass`) with three invoices.
- Drive the web UI with the repo's Playwright setup (`npx playwright test --project=chromium`) or a Playwright script.
- Stop only the processes this run started. Keep evidence outside the source tree.

## Features

- [Invoice export](./invoice-export.md): CSV export from the invoices page, CLI, and API.
```

## Feature example

```markdown file=invoice-export.md
# Invoice export

A signed-in user downloads their invoices as a CSV file.

## What it is

Exports every invoice visible to the user, one row per invoice, with columns number, customer, total, and status.

## How to reach it

- web: `/invoices` then the `Export CSV` button
- cli: `ledger export --format csv --output invoices.csv`
- api: `GET /api/invoices.csv` with the session cookie

## Setup

Seeded data from the index. Sign in as `demo@example.test`. For the API, reuse the browser session cookie or call `POST /api/login`.

## Key paths

- Export with three seeded invoices.
- Export with no invoices after `make seed-empty`: header row only.
- Export while signed out: web redirects to `/login`, API returns 401.

## Success looks like

The download is named `invoices.csv`, has a header row plus one row per seeded invoice, and totals match the invoices page. The CLI exits 0 and writes the same rows.

## Gotchas

- The button is disabled until the invoice list finishes loading; wait for the `Invoices` table, not a fixed delay.
- Totals are formatted in the CSV as plain decimals, not currency strings.

## Last checked

2026-10-10, revision `4f2c9a1`, web `/invoices` export with seeded data.
Status: verified
Evidence: `/tmp/ledger-evidence/export.png`, `/tmp/ledger-evidence/invoices.csv`.
```
