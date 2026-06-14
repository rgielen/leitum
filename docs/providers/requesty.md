# Requesty Provider

[Requesty](https://requesty.ai) is an LLM router that proxies requests to multiple providers.

## Setup

1. Get an API key from [requesty.ai](https://requesty.ai)
2. Set the environment variable: `export REQUESTY_API_KEY=your-key`
3. Run `leitum init` (uses Requesty as the default example)

## Configuration

```yaml
- name: requesty
  base_url: https://router.requesty.ai
  auth:
    token: ${REQUESTY_API_KEY}
    env_var: ANTHROPIC_AUTH_TOKEN
```

## Model naming

Requesty uses the format `<provider>/<model-id>`, e.g.:
- `anthropic/claude-sonnet-4-5`
- `anthropic/claude-opus-4-5`
- `anthropic/claude-haiku-4-5`

## Model discovery

Without a `models:` list in the config, leitum calls `GET https://router.requesty.ai/v1/models`
to discover available models. Results are cached for 24 hours.

Refresh with: `leitum refresh --provider requesty`

## Claude Code integration

Requesty accepts Claude Code's `ANTHROPIC_AUTH_TOKEN` env var by default.
The `ANTHROPIC_BASE_URL` is set to `https://router.requesty.ai`.
