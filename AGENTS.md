# Reefstack repository guidance

This repository is a set of workflow skills with a host-neutral core. Preserve proportional routing: small known edits stay direct; consequential work gets integration proof and independent review. User intent and permissions remain authoritative.

## Checks

- `python3 scripts/health.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/package.py --output <fresh-path>.zip`

Use Python standard-library APIs compatible with Python 3.9+. No web build or dev server is needed. Exclude Git history and private/local configuration from release archives. Do not install the skills or plugin, or alter global instructions, as a side effect of running checks.

Everything that ships lives in skills/: core procedures in skills/reefstack/references/, named host mechanics only in skills/reefstack/harness/, and the map lint in skills/map/scripts/. Links under skills/ stay inside skills/ so the folders install on their own (health enforces it). scripts/ and tests/ are development tooling. Reefstack ships no hooks. Name no models in skills. Read only references needed for the change. The coordinator skill stays under about 2,000 tokens (a test enforces it): new standing text replaces old text, and a rule whose failure stops recurring is deleted. Routing changes, including skill descriptions, require realistic cases rather than only string assertions.

Public claims must distinguish package validity, installation, triggering on each surface, and behavioral acceptance. Do not publish benchmark claims without comparative measurements.
