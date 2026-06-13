# Initial Specification Review — 2026-06-13

This document captures the review of the initial product specification for
`leitum` (a Python CLI that launches Claude Code against alternative LLM
routers), the open questions that emerged from the review, and the
pre-decisions that were used to author `CLAUDE.md` and the PRDs in `prd/`.

## Context

- Original specification: `intial-prompt.md` (German, user-authored).
- Outputs of this session: `CLAUDE.md` (English) and PRDs `00`–`07` in
  `prd/` (German).
- No code was written in this session — pre-implementation alignment only.

## Review findings

### 1. Flag collisions

- `-h` for `--haiku` collides with the universal `--help` short flag, which
  every standard CLI framework reserves.
- `-p` for `--provider` collides with Claude Code's own `-p`/`--print`
  short flag, which would create ambiguity when users want to use Claude
  Code's print mode through `leitum`.

### 2. Authentication mechanics

- The original specification did not fix which environment variable carries
  the auth token. Requesty uses `ANTHROPIC_AUTH_TOKEN`; other Anthropic-
  compatible routers may use `ANTHROPIC_API_KEY` or other names.
- A pre-existing `ANTHROPIC_API_KEY` on the user's shell could silently win
  over the provider's auth value if not actively scrubbed before launch.

### 3. Token storage

- Storing API tokens in plain text in `~/.config/leitum/api-providers.yaml`
  is a security risk and forecloses sharing the config across machines.
- The specification did not mention permission modes for any of the on-disk
  files.

### 4. "Context" semantics

- The spec referenced kubectl-style contexts but described behavior that
  matches a simple "remember last selection" model, not the kubectl model
  (which is a named bundle plus a `current-context` pointer).
- Two distinct interpretations existed: (A) remember last selection only,
  or (B) named, switchable profiles. Implementation effort differs by
  roughly 3×.

### 5. Model-slot UX

- The spec implied four sequential interactive selections per launch
  (start, opus, sonnet, haiku), which is tedious for daily use.
- "Last selection" was implied as a single global value, but each provider
  has a different model space, so "last model" only makes sense per
  provider.
- The spec did not say what happens if a slot remains unset — does `claude`
  launch with no `--model`? Does the env var get set to an empty value?

### 6. Model discovery via API

- The spec said "fetch the model list from the provider," but did not
  specify the endpoint, caching behavior, or fallback on failure. Different
  providers expose different endpoints (OpenAI-compatible `/v1/models`,
  Ollama `/api/tags`, etc.).

### 7. Curses or higher-level UI?

- "Curses" was named explicitly, but raw curses is verbose and brittle on
  modern terminals. Several high-quality TTY-prompt libraries exist that
  remove most of the friction.

### 8. Lifecycle commands

- The spec described `leitum claude` but not how the user creates,
  inspects, or removes providers. A bare-YAML workflow is viable but
  hostile to first-time users.

### 9. Pass-through arguments

- The spec did not explicitly define what should happen to extra arguments
  after `claude`. Without a rule, an invocation like `leitum claude
  --resume` would be ambiguous.

### 10. Language ambiguity for CLAUDE.md

- The spec set "documentation → English, PRDs → German" but did not
  classify `CLAUDE.md` itself.

### 11. Minor items

- Naming "START-MODELL" as a slot is awkward outside German; "main/primary"
  reads better in English documentation, but the slot identifier should
  stay machine-stable.
- No `--dry-run` or `--verbose` modes were specified, though both are
  cheap and standard.
- Python minimum version, license, build backend, packaging tools were not
  pinned.

## Decisions taken to author CLAUDE.md and the PRDs

The decisions below were either confirmed interactively with the user or
taken autonomously where the trade-off was small. Decisions confirmed by
the user are marked **[user]**; decisions taken autonomously and reported
back are marked **[auto]**.

### Flag layout and pass-through **[user]**

- `leitum`-own options must appear **before** the subcommand name; every
  argument after `claude` is forwarded unchanged to the `claude` binary.
- This eliminates the `-p` collision entirely: leitum's `-p` is consumed
  before `claude` ever sees it, and `claude`'s `-p` lives in the
  pass-through bucket.

### Haiku short flags **[user, revised]**

- `--haiku` short flag: `-k`.
- `--use-last-haiku` short flag: `-K`.
- `-h` remains `--help` per universal convention.
- (Initial draft used "no short flag" for `--haiku`; user revised to
  `-k`/`-K`.)

### Context model **[user]**

- v1 implements **last-selection-only**. No named profiles.
- `state.yaml` stores `last_provider` plus, per provider, the last
  selected model for each of the four slots.

### Model selection UX **[user]**

- A **single dialog** with four slot rows, not four sequential selects.
- Each slot can be set to "do not set", which omits the corresponding
  env var (and, for `start`, omits `--model` entirely).
- Pre-population per slot: explicit flag → `--use-last-*` → provider
  defaults → last state → `roles` match → "do not set".

### Interactive prompt library **[user]**

- `questionary` instead of raw curses. The selection-algorithm logic is
  factored out of the UI layer so it remains unit-testable without a TTY.

### Authentication scheme **[auto]**

- Per provider, `auth.token` plus an optional `auth.env_var` (default
  `ANTHROPIC_AUTH_TOKEN`). Tokens support `${VAR}` interpolation against
  the live shell environment so users can keep secrets outside the file.
- Before launch, `ANTHROPIC_API_KEY` is actively removed from the child
  environment unless the active provider's `auth.env_var` is exactly
  `ANTHROPIC_API_KEY`.

### File security **[auto]**

- `api-providers.yaml` and `state.yaml`: mode `0600`.
- Config directories: mode `0700`.
- On read, a permissions check warns if the file is more permissive than
  `0600` but does not silently rewrite.
- Tokens never appear in stdout, stderr, or any log line — including with
  `--verbose`. `leitum provider show --reveal-token` is the single opt-in
  path to display a token, with confirmation and a stderr warning.

### Model discovery **[auto]**

- API contract for v1: OpenAI-compatible `GET /v1/models` with bearer auth.
- Cache: `~/.cache/leitum/models/<provider>.json`, 24 hour TTL, JSON.
- `leitum refresh` clears the cache and re-fetches.
- On HTTP failure: stale cache is acceptable; without any cache, the
  command errors with a clear hint and exits with code 4.
- If the YAML defines a `models` list for the provider, the API is never
  contacted for that provider.

### Slot default behavior **[auto]**

- An unset `start` slot launches `claude` without `--model` — Claude Code
  uses its own default.
- Unset `opus` / `sonnet` / `haiku` slots simply omit the corresponding
  `ANTHROPIC_DEFAULT_*_MODEL` env var.

### "Last model" scoping **[auto]**

- The "last selection" for each model slot is stored **per provider**, not
  globally. Otherwise `--use-last-model` would suggest nonsense after a
  provider switch.

### Management subcommands **[auto]**

- `leitum init`, `leitum provider {list,show,add,remove}`,
  `leitum refresh`, `leitum doctor`, `leitum completions` are in scope for
  v1.
- `leitum doctor` is read-only diagnostics: it reports, never repairs.

### Diagnostics flags **[auto]**

- `--dry-run` prints the resolved child environment (token values
  redacted) and the final exec line, then exits without launching.
- `--verbose` / `-v` writes progress events to stderr, including resolved
  provider, set env-var names (never values), and the exec line.

### Tech-stack choices **[auto]**

- Python 3.11+.
- CLI: `typer`. Prompts: `questionary`. Validation: `pydantic` v2.
- YAML I/O: `ruamel.yaml` (preserves comments and order on write).
- HTTP: `httpx` (sync client by default).
- Tests: `pytest` + `pytest-mock` + `respx` + `freezegun`.
- Linting / formatting: `ruff`. Static typing: `mypy --strict`.
- Build backend: `hatchling`. Dev workflow: `uv`.

### Distribution **[auto]**

- Primary: PyPI as `leitum`, runnable through `uvx leitum`.
- Secondary: dedicated Homebrew tap. Homebrew-core submission is deferred.
- macOS is the reference platform; Linux must stay functional; Windows is
  not supported in v1.

### License **[user, revised]**

- **Apache 2.0**. SPDX identifier `Apache-2.0` in `pyproject.toml`,
  `LICENSE` and `NOTICE` files at the repository root.
- (Initial draft used MIT; user revised to Apache 2.0.)

### Language convention for CLAUDE.md **[auto]**

- `CLAUDE.md` is English, in line with the broader "documentation is
  English" rule. PRDs remain German, per explicit user instruction.

### Exit codes **[auto]**

- A defined ladder: 0 success, 2 argument error, 3 configuration error,
  4 unresolved provider/model, 5 `claude` binary missing, 130 user
  cancellation, otherwise pass-through from the launched process.

### Schema versioning **[auto]**

- Both `api-providers.yaml` and `state.yaml` carry `schema_version: 1`.
  Migrations land in `leitum/config/migrations/` with a `.bak` snapshot
  before any in-place rewrite.

## Items intentionally deferred

The following were considered and explicitly placed in the roadmap rather
than v1:

- macOS Keychain integration for token storage.
- Named, kubectl-style contexts/profiles.
- Additional agents (`copilot-cli`, `opencode`, `gemini-cli`).
- Provider presets beyond Requesty (OpenRouter, LiteLLM, Ollama).
- Homebrew-core submission.
- A `mkdocs`-based documentation site (v1 ships Markdown in `docs/`).

## Artifacts produced this session

- `CLAUDE.md`
- `prd/00-overview.md`
- `prd/01-configuration.md`
- `prd/02-cli.md`
- `prd/03-selection-flows.md`
- `prd/04-launch.md`
- `prd/05-management-commands.md`
- `prd/06-testing.md`
- `prd/07-packaging-and-docs.md`
- `.claude/history/260613-1729-Initial-Review.md` (this file)
