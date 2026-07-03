# Local Providers (llama.cpp, vLLM, and generic)

You can run Claude Code against other local inference engines such as **llama.cpp** (`llama-server`) and **vLLM** as long as they expose Anthropic-compatible endpoints.

## llama.cpp (`llama-server`)

The standard `llama-server` provides an Anthropic-compatible Messages API format out of the box.

### Setup via Preset

```bash
leitum provider add --preset llama-cpp
```

### Setup via Auto-Detection

If `llama-server` is running on its default port `8080`, you can detect it automatically:

```bash
leitum provider detect
```

### Manual Setup

Add the following block to your `~/.config/leitum/api-providers.yaml` file:

```yaml
- name: llama-cpp
  base_url: http://localhost:8080
  auth:
    token: local
    env_var: ANTHROPIC_AUTH_TOKEN
```

Ensure your `llama-server` is started with a sufficiently large context limit (e.g. `-c 32768` or `-c 65536`) to accommodate Claude Code's extensive prompts.

---

## vLLM

`vLLM` is a high-throughput and memory-efficient LLM serving engine. It provides an Anthropic-compatible Messages API.

### Setup via Preset

```bash
leitum provider add --preset vllm
```

### Setup via Auto-Detection

If `vLLM` is running on its default port `8000`, you can detect it automatically:

```bash
leitum provider detect
```

### Manual Setup

Add the following block to your `~/.config/leitum/api-providers.yaml` file:

```yaml
- name: vllm
  base_url: http://localhost:8000
  auth:
    token: local
    env_var: ANTHROPIC_AUTH_TOKEN
```

---

## Generic Local Provider Template

For any other local, Anthropic-compatible server running on a custom port or another framework, you can use the generic template.

### Setup via Preset

```bash
leitum provider add --preset local-generic
```

### Manual Configuration Example

```yaml
- name: local-generic
  base_url: http://localhost:8080      # Adjust port/host if necessary
  auth:
    token: local                       # Placeholder token, not a secret
    env_var: ANTHROPIC_AUTH_TOKEN
```

---

## Important Considerations for Local Models

### Context Length
Claude Code is a codebase agent. It reads multiple files and writes complex solutions, which consumes a vast amount of context.
- **Absolute Floor**: 32K context (`32768` tokens).
- **Sweet Spot**: 64K context (`65536` tokens).
Configure your server (vLLM, llama.cpp, etc.) to allow at least 32K context, otherwise your session will run out of space rapidly.

### Tool Calling Support
Your local model **must** natively support tool calling. If a model does not support tool calling:
- Claude Code will start up, but it will fail the very first time it tries to read or edit a file, run a shell command, or search directories.
- You will see failures such as empty/invalid tool calls or Claude Code being unable to complete any agentic task.
