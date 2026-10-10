# Codex delegation mechanics

Codex delegates when applicable project or skill instructions request it, so apply the triggers rather than waiting for a separate user request. Map roles to agent types: explorer to `explorer`; mechanical, worker, and hard_worker to `worker`; reviewer and critical_reviewer to a fresh agent assigned read-only review.

Pass model, effort, and `fork_turns: "none"` on every spawn with a self-contained brief. A full-history fork inherits the parent's model and cannot take another. A custom agent file that shadows `explorer` or `worker` can override the requested model; disclose a mismatch. Respect the session's concurrent thread cap, wait on completion events instead of polling, and do not install custom agents or edit global configuration unless the user asks.
