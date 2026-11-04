# Installing Reefstack in Codex

Install one copy; two installs list every skill twice.

- **User skills folder:** link or copy each folder under the Reefstack checkout's `skills/` into `~/.agents/skills/`, keeping them siblings. Codex follows the links to the checkout and namespaces the skills after its `.codex-plugin/plugin.json`, so linked skills are `$reefstack:reefstack`; copied folders are `$reefstack` and need recopying to update.
- **Plugin:** `codex plugin marketplace add thetylerreiff/reefstack`, then `codex plugin add reefstack@reefstack`. The coordinator is `$reefstack:reefstack`. `codex plugin list` shows whether it is installed.
- **One repository or cloud tasks:** a cloud task sees only its repository, so copy the folders into that repository's `.agents/skills/` and commit them with the user's approval. The coordinator is `$reefstack`.

`codex debug prompt-input "<request>"` from the target directory renders the model-visible prompt without a model call; its skill list shows what actually loaded and under which names.

Codex uses a skill only when a turn names it or the task clearly matches its description, and does not carry it to later turns. For every turn, the user's `~/.codex/AGENTS.md` or a repository's `AGENTS.md` can carry `For software engineering work, use the reefstack skill.` Add it only with the user's approval.

Automations are heartbeat turns in an existing thread and get no skill unless the prompt names it. Watches created by 0.3.x relied on a removed hook and lack that line; those created by 0.2.x also point at removed `.reefstack/tasks/` records. With the user's approval, recreate them through [PR watch](pr-watch.md). Hook trust entries left in `~/.codex/config.toml` by 0.3.x are inert.
