# AGENTS.md

## Project overview

This repository is a Discord meme bot built around a single bot entrypoint in [bot.py](bot.py). The bot loads command extensions from the [cogs](cogs) directory, reads runtime config from [config.py](config.py), and generates meme images through helpers like [image_handler.py](image_handler.py), [views.py](views.py), [layoutviews.py](layoutviews.py), and [dumpy.py](dumpy.py).

The project is intentionally small and script-driven. Prefer minimal, local changes that match the existing command-oriented structure instead of introducing new frameworks or large architecture refactors.

## Key files

- [README.md](README.md) — project summary and repo-level context.
- [bot.py](bot.py) — main Discord bot, command registration, startup flow, and event handlers.
- [config.py](config.py) — CLI flags and configuration loading.
- [cogs/discordinfo.py](cogs/discordinfo.py) and [cogs/gifcommands.py](cogs/gifcommands.py) — example extension-based commands.
- [justfile](justfile) — repo commands for linting and formatting.
- [requirements.txt](requirements.txt) — pinned Python dependencies.

## Development workflow

Use the repo's existing commands when validating or formatting changes:

- `just lint` runs the Python checks configured in [justfile](justfile): isort, pyupgrade, autoflake, and flake8.
- `just format` runs Black on the project.

There are no dedicated unit tests in this repo; validate with the smallest relevant Python command or the existing lint/format workflow when making changes.

## Architecture and conventions

- The bot is created in [bot.py](bot.py) and started by `client.run(TOKEN)` near the end of the file.
- Extensions are auto-loaded from `cogs/*.py` via `glob.glob("cogs/*.py")` in `setup_hook()`.
- Commands are registered with Discord application commands using `@client.tree.command(...)` or `@app_commands.command(...)` in cog classes.
- Shared command decorators from [decorators.py](decorators.py) are used widely for logging and timing; keep that pattern when adding new commands.
- Runtime configuration is chosen with the `--prod` flag in [config.py](config.py): dev uses `config-dev.ini`, prod uses `config.ini`.
- Image/meme generation is handled by dedicated helpers rather than being embedded inline in commands; follow that separation when adding new functionality.

## Working rules for agents

- Match the existing naming and Discord command style; do not introduce alternate bot patterns unless the task specifically requires it.
- Keep bot commands and image logic near the existing module boundaries instead of creating a new app framework.
- Preserve the repo's low-overhead style: direct Python scripts, small helpers, and config-driven runtime behavior.
- When changing config behavior, keep both `config.ini` and `config-dev.ini` semantics aligned with the parser in [config.py](config.py).
- Prefer targeted edits and minimal dependencies over broader cleanup or refactors that are unrelated to the task.

## Helpful references

- [README.md](README.md)
- [justfile](justfile)
- [config.py](config.py)
- [bot.py](bot.py)
- [decorators.py](decorators.py)
