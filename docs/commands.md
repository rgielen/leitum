# CLI Commands Reference

## Global Options

These options must appear **before** the subcommand:

```
leitum [OPTIONS] <subcommand> [ARGS...]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--provider <name>` | `-p` | Set provider |
| `--use-last-provider` | `-P` | Reuse last used provider |
| `--model <id>` | `-m` | Set START model |
| `--use-last-model` | `-M` | Reuse last START model |
| `--opus <id>` | `-o` | Set OPUS model |
| `--use-last-opus` | `-O` | Reuse last OPUS model |
| `--sonnet <id>` | `-s` | Set SONNET model |
| `--use-last-sonnet` | `-S` | Reuse last SONNET model |
| `--haiku <id>` | `-k` | Set HAIKU model |
| `--use-last-haiku` | `-K` | Reuse last HAIKU model |
| `--refresh` | `-r` | Refresh model cache before selection |
| `--no-project-config` | | Ignore `leitum.yaml` |
| `--project-config <path>` | | Use alternative project config |
| `--dry-run` | | Print resolved env and exec line |
| `--verbose` | `-v` | Verbose stderr logging |
| `--version` | | Show version |
| `--help` | `-h` | Show help |

## leitum claude

Launch Claude Code. All arguments after `claude` are passed through unchanged.

```bash
leitum claude
leitum -p requesty claude --resume
leitum -p requesty -m anthropic/claude-sonnet-4-5 claude -p "Explain this code"
leitum --dry-run -p requesty claude
leitum -P -M claude   # reuse last provider and model
```

## leitum init

Initialize config directory and example `api-providers.yaml`.

```bash
leitum init
leitum init --force --yes   # overwrite without prompt
```

## leitum provider list

List all configured providers.

```bash
leitum provider list
```

## leitum provider show

Show provider configuration (token redacted).

```bash
leitum provider show requesty
leitum provider show requesty --reveal-token
```

## leitum provider add

Interactively add a new provider.

```bash
leitum provider add
```

## leitum provider remove

Remove a provider (with confirmation).

```bash
leitum provider remove requesty
leitum provider remove requesty --yes
```

## leitum refresh

Clear model cache and re-fetch.

```bash
leitum refresh                     # all providers
leitum refresh --provider requesty  # specific provider
```

## leitum doctor

Run sanity checks.

```bash
leitum doctor
leitum doctor --project-config path/to/leitum.yaml
```

## leitum completions

Print shell completion script.

```bash
leitum completions zsh > ~/.zfunc/_leitum
leitum completions bash > /etc/bash_completion.d/leitum
```
