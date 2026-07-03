# Ollama Provider

[Ollama](https://ollama.com) is a tool that lets you run large language models locally. Since its 2026-01 release, Ollama natively supports the Anthropic Messages API, making it compatible with Claude Code and leitum without any translation proxy.

## Setup

### Prerequisites

- **Ollama**: Ensure you have Ollama installed (January 2026 release or newer).
- **Model**: Pull a local model that supports tool calling (e.g., `qwen2.5-coder:14b` or `llama3.1`). Claude Code is an agentic tool and relies heavily on tool calling to function correctly.

```bash
ollama pull qwen2.5-coder:14b
```

### Option A: Interactive Wizard

Run the interactive wizard, select **Ollama (local)** (or select a custom provider if presets are not yet available), and follow the prompts:

```bash
leitum provider add
```

### Option B: Manual Setup

Add the following block to your `~/.config/leitum/api-providers.yaml` file:

```yaml
- name: ollama
  base_url: http://localhost:11434
  auth:
    token: ollama
    env_var: ANTHROPIC_AUTH_TOKEN
  extra_env:
    OLLAMA_CONTEXT_LENGTH: "32768"
```

Because Ollama runs locally and does not require actual authentication, a placeholder token like `ollama` is used. This is safe to keep in plain text in your configuration.

*Note: Automated detection (`leitum provider detect`) and preset commands (`leitum provider add --preset ollama`) are upcoming features and will be available in a future release.*

## Model Discovery

With the Ollama provider configured, leitum will discover your locally pulled models via the `GET http://localhost:11434/v1/models` endpoint.

To clear or force refresh your local models:

```bash
leitum refresh --provider ollama
```

## Context Length

Claude Code is context-heavy as it reads files, performs searches, and tracks state.
- **Minimum**: 32K context is the absolute floor. This is set automatically via the `OLLAMA_CONTEXT_LENGTH: "32768"` environment variable under `extra_env`.
- **Recommended**: 64K or larger is the sweet spot for smoother, multi-step agent operations.

## Model Choice & Tool Support

Ensure the model you choose supports native tool calling. If you select a model without tool-use capability, Claude Code will fail to perform filesystem actions, write files, or run command-line tools.

Recommended local models:
- `qwen2.5-coder:14b` or larger
- `llama3.1` (8b/70b)
- `mistral-nemo`
