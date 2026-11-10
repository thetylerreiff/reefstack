# Codex delegation mechanics

Codex delegates when applicable project or skill instructions request it, so apply Deliver's triggers rather than waiting for a separate user request. Use the `explorer` agent type for read-only questions and `worker` for writable pieces; a reviewer is a fresh agent assigned read-only review.

Pass `fork_turns: "none"` on every spawn with a self-contained brief; a full-history fork inherits the parent's context and model. To watch a pull request after opening or pushing to it, follow [PR watch](pr-watch.md). Respect the session's concurrent thread cap, wait on completion events instead of polling, and do not install custom agents or edit global configuration unless the user asks.

A spawn that returns an error started nothing: there is no thread to wait on and no reply will come. Do not wait on it or describe its result. Record the exact error and continue without that helper: do the piece yourself, or for a reviewer run a focused self-check and report `Review: not run (spawn failed: <error>)`. A helper's result is only the reply you actually received.
