# LM Studio Provider

[LM Studio](https://lmstudio.ai) is a desktop application for running local LLMs. From version `0.4.1` onwards, LM Studio provides an Anthropic-compatible `/v1/messages` endpoint, allowing you to run Claude Code locally with leitum.

## Setup

### Prerequisites

- **LM Studio**: Ensure you have LM Studio v0.4.1 or newer installed.
- **Model**: Load a model that supports tool calling (e.g., `Qwen/Qwen2.5-Coder-14B-Instruct` or `meta-llama/Llama-3.1-8B-Instruct`). Claude Code relies heavily on tool calling to interact with your codebase.
- **Local Server**: Start the local server inside the LM Studio application (typically runs on port `1234`).

### Option A: Automatic Detection (Recommended)

Start the local server in LM Studio, then run:

```bash
leitum provider detect
```

leitum will scan local ports, discover LM Studio at `http://localhost:1234`, detect your loaded/available models, and offer to add it.

### Option B: Preset Command

You can add LM Studio using the built-in preset:

```bash
leitum provider add --preset lm-studio
```

Or run the interactive wizard, select **LM Studio (local)**, and follow the prompts:

```bash
leitum provider add
```

### Option C: Manual Setup

Add the following block to your `~/.config/leitum/api-providers.yaml` file:

```yaml
- name: lm-studio
  base_url: http://localhost:1234
  auth:
    token: lmstudio
    env_var: ANTHROPIC_AUTH_TOKEN
```

Because LM Studio runs locally and does not require actual authentication, a placeholder token like `lmstudio` is used. This is safe to keep in plain text in your configuration.

## Model Discovery

With the LM Studio provider configured, leitum will discover your loaded/available models via the `GET http://localhost:1234/v1/models` endpoint.

To clear or force refresh your local models:

```bash
leitum refresh --provider lm-studio
```

## Context Length

Claude Code is context-heavy as it reads files, performs searches, and tracks state.
- **Minimum**: 32K context is the absolute floor.
- **Recommended**: 64K or larger is the sweet spot for smoother, multi-step agent operations.
- Make sure to configure the **Context Length** setting inside LM Studio when loading your model.

## Model Choice & Tool Support

Ensure the model you load in LM Studio supports native tool calling. If you select a model without tool-use capability, Claude Code will fail to perform filesystem actions, write files, or run command-line tools.

Recommended local models:
- `Qwen/Qwen2.5-Coder-14B-Instruct`
- `meta-llama/Llama-3.1-8B-Instruct`
