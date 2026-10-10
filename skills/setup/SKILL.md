---
name: setup
description: Check a Reefstack installation, automatic context loading, hook trust, and available helper models during onboarding or repair.
---

# Reefstack setup

This is initial onboarding or repair, never a prerequisite to ordinary engineering work. Run `python3 scripts/health.py` from the installed plugin root to validate packaged files and exercise the hooks. That check does not prove the host runtime loaded them.

Inspect the host's supported plugin installation and hook trust UI. Enabled hooks require the user to review and trust their definition. Never write trust records or bypass trust on the user's behalf. Test a fresh engineering chat and a resumed/compacted chat, confirming actual context delivery and proportional behavior before claiming automatic activation.

Enumerate the actual models and reasoning levels supported by the current agent tool. The parent model remains selected by the user. Compare them with the packaged role defaults in `settings.json` (explorer, mechanical, worker, heavy_worker, reviewer, critical_reviewer). Disclose unavailable defaults and use explicit available alternatives. Do not install custom agents or rewrite global configuration simply to select models already supported by spawn requests.

Optional user overrides live in `settings.json` under the host's plugin data directory (the README names it per host). It supports `enabled` and partial entries under `models`. Change it only when the user requests a preference change; preserve unspecified settings. Do not edit the installed cache as a durable preference store.

If the user requests installation, add the supplied local marketplace through the host's supported plugin interface, then install and enable Reefstack. Do not silently edit global instruction files. Disabling/uninstalling the plugin should remove its runtime hook contribution; verify that in a new chat. Context already delivered to an open conversation remains there until the session is refreshed.

Consult the packaged README for installation, checks, supported surfaces, and evaluation limitations. Report package validity, installation, enablement, hook trust, actual context delivery, and behavioral validation separately.
