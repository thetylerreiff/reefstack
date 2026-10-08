# Reefstack repository guidance

This repository is a workflow plugin with a role-based core and a local Python adapter. Preserve proportional routing: small known edits stay direct; consequential work gets integration proof and independent review. User intent and permissions remain authoritative.

## Checks

- `python3 scripts/health.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/package.py --output <fresh-path>.zip`

Use Python standard-library APIs compatible with Python 3.9+. No web build or dev server is needed. Exclude Git history and private/local configuration from release archives. Do not install the plugin, alter global instructions, or trust hooks as a side effect of running checks.

Core procedures live in skills/ and references/; named host/model mechanics live in harness/, hooks/, scripts/, and settings.json. Read only references needed for the change. Hook changes require tests of actual command transport; routing changes require realistic cases rather than only string assertions.

Public claims must distinguish package validity, installation, hook trust, native context delivery, and behavioral acceptance. Do not publish benchmark claims without comparative measurements.
