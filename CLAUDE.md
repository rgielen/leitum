# leitum — Agent Working Instructions

`leitum` is a small Python CLI that launches coding agents (initially Claude Code)
against alternative LLM routers/providers (initially Requesty). It mirrors the
ergonomics of `ollama launch` and `omlx launch`: the user runs `leitum claude` and
leitum prepares the environment so that Claude Code talks to the chosen provider
and models instead of the Anthropic API.

This file is loaded automatically by Claude Code at session start. Read it first.

## Languages

- **Code, documentation, comments, README, commit messages, PR titles/bodies, issue
  titles/bodies, code review comments**: English.
- **Product Requirements Documents (PRDs in `prd/`)**: German. They reflect the
  language of the original prompt.
- **Conversation with the user**: whatever language the user writes in. The current
  user writes German; respond in German unless asked otherwise.

When in doubt: code-facing artifacts are English, product-thinking artifacts are
German.

## Product scope (v1)

- One agent: Claude Code.
- One reference provider: [Requesty](https://docs.requesty.ai/integrations/claude-code).
  The configuration model must already generalize to other Anthropic-compatible
  routers (OpenRouter, LiteLLM, local Ollama in Anthropic-shim mode).
- Configuration in `~/.config/leitum/`, runtime state in `~/.local/state/leitum/`
  (XDG), model cache in `~/.cache/leitum/`. An optional project-local
  `leitum.yaml` in the current working directory pins provider/model choices
  per repository (see PRD 01 and PRD 03). It is checked into version control
  and must never contain tokens.
- Interactive TTY selection where ambiguous; non-interactive when fully specified
  by flags or by a single-option configuration.

Out of scope for v1: copilot-cli, opencode, other agents; macOS Keychain;
named/multi-context profiles (kubectl-style); GUI; Windows support.

## Tech stack

- Python 3.11+.
- CLI framework: [`typer`](https://typer.tiangolo.com/).
- Interactive prompts: [`questionary`](https://questionary.readthedocs.io/).
- Config validation: [`pydantic` v2](https://docs.pydantic.dev/).
- YAML: [`ruamel.yaml`](https://yaml.readthedocs.io/) (preserves comments/order).
- HTTP for model discovery: [`httpx`](https://www.python-httpx.org/).
- Tests: `pytest`, `pytest-mock`, fake `claude` binary via fixture.
- Build backend: `hatchling` with `pyproject.toml`.
- Package/dev workflow: `uv` (lockfile, sync, run).
- License: Apache 2.0.

## Distribution

- Primary: PyPI as `leitum`, runnable via `uvx leitum`.
- Secondary: Homebrew via a dedicated tap (`brew tap <owner>/leitum`).
  Homebrew-core submission is a later goal, not v1.
- Reference platform: current macOS. Linux must keep working; Windows is not
  supported in v1.

## CLI shape

```
leitum [LEITUM_OPTS] <subcommand> [SUBCOMMAND_ARGS_PASSED_THROUGH]
```

- `leitum claude [...]` launches Claude Code. Every argument that follows
  `claude` is passed through to the `claude` binary unchanged. Leitum's own
  flags must appear **before** the subcommand name.
- Management subcommands (`leitum provider …`, `leitum doctor`, `leitum refresh`,
  `leitum init`) are first-class and do not pass through.
- Use `--dry-run` to print the resolved environment and final exec line without
  launching. Use `-v`/`--verbose` for progress logging on stderr.

## Behavioral rules

- **Never** write a token, API key, or any secret to logs, stdout, or to files
  outside `~/.config/leitum/api-providers.yaml`. Redact in verbose output.
- Files in `~/.config/leitum/` must be created with mode `0600`. If an existing
  file has weaker permissions, warn and offer to fix; do not silently rewrite.
- Before launching, strip a host-inherited `ANTHROPIC_API_KEY` from the child
  environment so it cannot override the provider's auth.
- The user's last interactive selections (provider, and per-provider models) are
  persisted to `~/.local/state/leitum/state.yaml`. Treat this file as cache:
  recoverable on loss, schema-versioned (`schema_version: 1`).
- Model discovery via API is **only** used if the provider has no model list in
  YAML. Results are cached under `~/.cache/leitum/models/<provider>.json` with a
  24h TTL; `leitum refresh` clears the cache.

## Coding conventions

- Type hints on all public functions. `mypy --strict` should pass.
- Format with `ruff format`, lint with `ruff check`. Keep both clean before
  commit.
- Module layout under `src/leitum/`:
  - `cli.py` (typer app, root command, pass-through plumbing)
  - `config/` (pydantic models, YAML I/O, paths, env interpolation)
  - `state.py` (last-used persistence)
  - `providers/` (model discovery, HTTP, cache)
  - `selection/` (provider + model interactive selection)
  - `launch.py` (env composition, exec)
  - `commands/` (subcommand handlers: claude, provider, doctor, refresh, init)
- Tests in `tests/`, mirroring the source tree.
- No emojis in code or docs.
- Comments only when the *why* is non-obvious. Don't comment what the code says.

## Git workflow

- `main` is the default branch and always green.
- Feature branches: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Commit messages: imperative, English, Conventional-Commits style
  (`feat: …`, `fix: …`, `docs: …`, `test: …`, `refactor: …`, `chore: …`).
- One logical change per commit. Squash trivia before opening a PR.
- PR titles in the same Conventional-Commits style; PR bodies in English with a
  short summary and a test plan checklist.
- **Never squash-merge automatically.** When merging a PR, preserve the
  individual commits (merge commit or fast-forward) so every step stays
  documented in `main`'s history. Only use a squash merge if the user explicitly
  asks for one in that instance.
- **Always delete the PR branch after merge.** The repository has
  `delete_branch_on_merge` enabled, so the **remote** head branch is removed
  automatically on merge. The matching **local** cleanup is manual and must
  always be done. Run it from the **primary checkout**, never from inside the
  branch's own worktree (`gh pr merge --delete-branch` fails when invoked from
  within the worktree it is trying to remove):

  ```bash
  git worktree remove <path>     # only if the branch had a worktree
  git branch -d <branch>         # -D only when intentionally discarding work
  git fetch origin --prune       # drop stale remote-tracking refs
  ```

  After a merge, no branch other than `main` should remain locally or on the
  remote unless it has unmerged work.

## When you make changes

1. If you change observable CLI behavior, update `README.md` and any affected
   PRD.
2. If you change a YAML schema, bump the schema version and document the
   migration in the PRD for configuration.
3. Run `ruff format`, `ruff check`, `mypy --strict`, and `pytest` before
   declaring a task done. State explicitly when any check is skipped and why.
4. Manual smoke test for Claude-launch changes: `leitum --dry-run claude` and
   verify the printed environment matches expectations.

## PRDs

The authoritative product specification lives in `prd/`. Read the matching PRD
before changing the corresponding area of the code, and update it when the
product behavior changes.
