# leitum

[![PyPI version](https://img.shields.io/pypi/v/leitum.svg)](https://pypi.org/project/leitum/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## What is leitum?

`leitum` is a small CLI tool that launches [Claude Code](https://docs.claude.com/en/docs/claude-code/quickstart)
against alternative LLM routers and providers (Requesty, OpenRouter, LiteLLM, local Ollama, etc.)
instead of the Anthropic API directly. It mirrors the ergonomics of `ollama launch` and `omlx launch`:
prepend `leitum` to your `claude` invocation and get your chosen provider and models configured automatically.

## Install

```bash
# via uvx (no install needed)
uvx leitum --version

# via pip
pip install leitum

# via Homebrew
brew tap rgielen/taps
brew install leitum
```

## Quickstart

```bash
# Initialize config directory and example providers file
leitum init

# Set your API key
export REQUESTY_API_KEY=your-key-here

# Launch Claude Code via Requesty
leitum claude

# Dry-run: see what would happen without launching
leitum --dry-run claude
```

## Configuration

Config lives at `~/.config/leitum/api-providers.yaml` (XDG). Example:

```yaml
schema_version: 1
providers:
  - name: requesty
    base_url: https://router.requesty.ai
    auth:
      token: ${REQUESTY_API_KEY}
    defaults:
      start: anthropic/claude-sonnet-4-5
    models:
      - id: anthropic/claude-sonnet-4-5
        roles: [sonnet, start]
      - id: anthropic/claude-opus-4-5
        roles: [opus]
      - id: anthropic/claude-haiku-4-5
        roles: [haiku]
```

See [docs/configuration.md](docs/configuration.md) for the full schema reference.

Pin provider and models per repository with `leitum.yaml` (checked into version control):

```yaml
schema_version: 1
provider: requesty
models:
  start: anthropic/claude-sonnet-4-5
```

Or let leitum write it for you: run `leitum -l claude`, make your selection, and
the resolved provider and models are saved to `leitum.yaml` (comments and
`extra_env` in an existing file are preserved, and the global state is left
untouched).

### Project-local secrets with `.leitumenv`

Place a `.leitumenv` file in your project root to supply API tokens
automatically on every `leitum claude` invocation — without direnv or manual
shell exports.

> **Security:** `.leitumenv` is executed as a bash script, so only use it in
> repositories you trust. Never check it into version control.

```bash
# .leitumenv — never commit this file

# Plain assignment (no shell needed)
export REQUESTY_API_KEY=rq-...

# Command substitution — fetch the token from 1Password on every launch
export REQUESTY_API_KEY="$(op read op://vault/requesty/Token)"

# Any bash expansion works
MY_CUSTOM_VAR=some_value
```

leitum sources this file via `bash` before loading any config, so `${VAR}`
references in `api-providers.yaml` and `leitum.yaml` resolve against its values.
All bash expansions are supported, including `$(...)`.

Behaviour:
- Shell environment takes precedence: a variable already set in your shell is
  never overwritten by `.leitumenv`.
- Lines starting with `#` and blank lines are ignored.
- A leading `export ` prefix is accepted (but not required — `set -a` exports
  all assignments automatically).
- Use `--no-dotenv` to skip loading the file for a single invocation.

**Add `.leitumenv` to your project's `.gitignore`** to prevent accidental
commits of tokens. leitum's own `.gitignore` already includes it.

## CLI Reference

```
leitum [OPTIONS] <subcommand> [ARGS...]
```

Global options (before the subcommand):

| Flag | Short | Effect |
|------|-------|--------|
| `--provider <name>` | `-p` | Set provider |
| `--use-last-provider` | `-P` | Reuse last provider |
| `--model <id>` | `-m` | Set START model |
| `--use-last-model` | `-M` | Reuse last START model |
| `--opus <id>` | `-o` | Set OPUS model |
| `--sonnet <id>` | `-s` | Set SONNET model |
| `--haiku <id>` | `-k` | Set HAIKU model |
| `--refresh` | `-r` | Refresh model cache |
| `--no-project-config` | | Ignore leitum.yaml |
| `--no-dotenv` | | Skip loading .leitumenv from CWD |
| `--save-local` | `-l` | Save the resolved selection to leitum.yaml instead of global state |
| `--dry-run` | | Print env + exec line, do not launch |
| `--verbose` | `-v` | Verbose logging on stderr |

Subcommands: `claude`, `provider list/show/add/remove`, `refresh`, `doctor`, `init`, `completions`.

See [docs/commands.md](docs/commands.md) for details.

## Providers

- [Requesty](docs/providers/requesty.md)
- Local Providers (fully supported):
  - [Ollama](docs/providers/ollama.md)
  - [LM Studio](docs/providers/lm-studio.md)
  - [llama.cpp, vLLM, and other local models](docs/providers/local.md)

## Troubleshooting

Run `leitum doctor` for a full sanity check. See [docs/troubleshooting.md](docs/troubleshooting.md).

## Contributing

See [CLAUDE.md](CLAUDE.md) and the PRDs in [prd/](prd/) for the authoritative specification. Also see the [Roadmap](docs/roadmap.md) for planned and shipped features.

## License

Apache 2.0 — see [LICENSE](LICENSE).
