# Codex delegation mechanics

Codex delegates when applicable project or skill instructions request it, so apply the triggers rather than waiting for a separate user request. Map roles to available agent types: explorer to `explorer`, worker and mechanical worker to `worker`, reviewer to a fresh agent assigned read-only review.

Pass model and effort explicitly on each spawn. These override global agent defaults, but a custom agent file can override the requested model and effort, including when it shadows `explorer` or `worker`. Check the effective configuration where the host exposes it; disclose a mismatch and choose an appropriate unshadowed agent when available. A read-only custom profile is a requested sandbox configuration, not an unconditional enforcement guarantee: live parent permission overrides can take precedence. Respect the actual effective permission mode and the read-only assignment.

Full-history forks inherit the parent's model in environments that expose that behavior. Use a fresh agent with a self-contained brief when the role needs a different model. Respect the session's concurrent thread cap. Use completion events or the supported wait mechanism; avoid repeated status polling or resuming agents merely to check them. Do not install custom agents or edit global configuration unless the user asks.
