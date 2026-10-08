---
name: diagnose
description: Reproduce an engineering failure, isolate its mechanism from runtime evidence, and define the smallest justified fix and regression check.
---

# Diagnose

Reproduce on the relevant surface or explain the specific unavailable boundary. Inspect actual state and logs. Form hypotheses and choose observations that eliminate them; do not keep adding plausible fixes without falsifying their premise.

Distinguish exact commit, configuration, target environment, and runtime observations when they affect causality. A restart or passing unit test does not by itself establish a cause. Do not access credentials or mutate shared environments merely to improve a diagnosis.

If two fixes sharing a premise fail the same check, state that premise and gather evidence about it before a third attempt. Surface a missing contract or asymmetric ownership rather than compensate with retries.

A diagnosis request ends with evidence-backed findings. When a fix is authorized, make the smallest durable change and rerun the original reproduction. Add a focused regression check when it can meaningfully capture the failure. Use [verify](../verify/SKILL.md) and add independent review only at the depth justified by the actual change.
