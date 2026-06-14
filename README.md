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

# via Homebrew (own tap)
brew tap <owner>/leitum
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
| `--dry-run` | | Print env + exec line, do not launch |
| `--verbose` | `-v` | Verbose logging on stderr |

Subcommands: `claude`, `provider list/show/add/remove`, `refresh`, `doctor`, `init`, `completions`.

See [docs/commands.md](docs/commands.md) for details.

## Providers

- [Requesty](docs/providers/requesty.md)

## Troubleshooting

Run `leitum doctor` for a full sanity check. See [docs/troubleshooting.md](docs/troubleshooting.md).

## Contributing

See [CLAUDE.md](CLAUDE.md) and the PRDs in [prd/](prd/) for the authoritative specification.

## License

Apache 2.0 — see [LICENSE](LICENSE).
