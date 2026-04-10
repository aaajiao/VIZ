<!--
Keep this file short. Anthropic recommends concise, structured project instructions
and explicitly suggests importing AGENTS.md when a repo already uses it.
-->

@AGENTS.md

## Claude Code

- This file is the Claude Code entrypoint for the repository. Keep shared project instructions in `AGENTS.md` so Codex and Claude Code read the same rules.
- Put Claude-specific additions here instead of duplicating architecture, workflow, or coding-standard content from `AGENTS.md`.
- Run commands from the repository root when possible.
- Primary validation commands:
  - `pytest tests/ -v`
  - `python -m build`
  - `viz generate --emotion euphoria --seed 42 --output-dir ./media`
- Use `CLAUDE.local.md` for uncommitted machine-local preferences, secrets, sandbox URLs, or personal test data.
