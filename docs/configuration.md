# Configuration Reference

## File Locations (XDG)

| File | Path |
|------|------|
| Provider config | `$XDG_CONFIG_HOME/leitum/api-providers.yaml` (default: `~/.config/leitum/`) |
| State | `$XDG_STATE_HOME/leitum/state.yaml` (default: `~/.local/state/leitum/`) |
| Model cache | `$XDG_CACHE_HOME/leitum/models/<provider>.json` (default: `~/.cache/leitum/`) |
| Project config | `$CWD/leitum.yaml` (optional) |

## api-providers.yaml

```yaml
schema_version: 1
providers:
  - name: requesty           # lowercase, kebab-case, unique
    base_url: https://router.requesty.ai
    auth:
      token: ${REQUESTY_API_KEY}    # supports ${VAR} and ${VAR:-default}
      env_var: ANTHROPIC_AUTH_TOKEN  # variable Claude Code reads (default)
    defaults:
      start: anthropic/claude-sonnet-4-5
      opus: anthropic/claude-opus-4-5
      sonnet: anthropic/claude-sonnet-4-5
      haiku: anthropic/claude-haiku-4-5
    models:                    # optional; skips API discovery if present
      - id: anthropic/claude-sonnet-4-5
        display: "Sonnet 4.5"
        roles: [sonnet, start]  # hint for pre-selection
      - id: anthropic/claude-opus-4-5
        display: "Opus 4.5"
        roles: [opus]
      - id: anthropic/claude-haiku-4-5
        display: "Haiku 4.5"
        roles: [haiku]
    extra_env:                 # optional extra environment variables
      ANTHROPIC_CUSTOM_HEADERS: "x-leitum: 1"
```

### Token interpolation

Values support `${VAR}` and `${VAR:-default}` syntax:
- `${REQUESTY_API_KEY}` — required variable; error if not set
- `${REGION:-eu-central-1}` — optional variable with fallback

### Model slots

Claude Code uses four model "slots":

| Slot | ENV variable | Flag |
|------|-------------|------|
| start | `--model` | `-m` |
| opus | `ANTHROPIC_DEFAULT_OPUS_MODEL` | `-o` |
| sonnet | `ANTHROPIC_DEFAULT_SONNET_MODEL` | `-s` |
| haiku | `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `-k` |

## leitum.yaml (Project Config)

Checked into the repository. Never put tokens here.

```yaml
schema_version: 1
provider: requesty        # optional; must exist in api-providers.yaml
models:
  start: anthropic/claude-sonnet-4-5
  opus: anthropic/claude-opus-4-5
extra_env:
  PROJECT_REGION: ${AWS_REGION:-eu-central-1}
```

This file pins provider and models for the repository. It overrides `state.yaml`
but is itself overridden by explicit CLI flags.

## state.yaml

Written automatically. Do not edit manually.

```yaml
schema_version: 1
last_provider: requesty
providers:
  requesty:
    models:
      start: anthropic/claude-sonnet-4-5
      opus: anthropic/claude-opus-4-5
    last_used: "2026-06-14T10:00:00+00:00"
```

## Model cache

Stored at `~/.cache/leitum/models/<provider>.json`. TTL: 24 hours.
Clear with `leitum refresh`.
