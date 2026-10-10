# Pantry verification map

How agents reach and check Pantry's user-facing features. Read this index, then the feature file for the change.

## Launch

- Start: `PANTRY_DATA=$(mktemp -d) PANTRY_PORT=8765 python3 -m pantry` in the background; it seeds Rice (4), Olive oil (1), and Black beans (2).
- Ready when `curl -fsS http://127.0.0.1:8765/healthz` returns `ok`.
- Drive the pages with a headless browser (Playwright) when one is available; otherwise use `curl` for server-rendered HTML.
- Stop only the server process this run started. Keep evidence outside the project.

## Features

- [Items list](./items.md): view and add pantry items.
- [Items export](./items-export.md): download the items as CSV.
