# Troubleshooting

## Quick check

```bash
leitum doctor
```

This runs all checks and suggests fixes.

## Common errors

### Exit code 3: Config not found

```
Error: providers config not found at ~/.config/leitum/api-providers.yaml. Run 'leitum init' first.
```

Run `leitum init`.

### Exit code 3: Missing environment variable

```
Error: Required env var `REQUESTY_API_KEY` not set
```

Export the variable: `export REQUESTY_API_KEY=your-key`

### Exit code 4: Model discovery failed

No models available and API unreachable. Add a `models:` list to the provider in
`api-providers.yaml` to avoid API calls, or check network connectivity.

### Exit code 5: claude not found

```
Error: 'claude' binary not found in PATH.
```

Install Claude Code: https://docs.claude.com/en/docs/claude-code/quickstart

### Exit code 2: Unknown provider

```
Error: unknown provider 'foo'. Known providers: requesty
```

Check the provider name: `leitum provider list`

### api-providers.yaml permissions warning

```
Warning: ~/.config/leitum/api-providers.yaml has permissions 0o644.
```

Fix: `chmod 600 ~/.config/leitum/api-providers.yaml`

## Debugging

Use `--verbose` and `--dry-run` together for a full trace without launching:

```bash
leitum --dry-run --verbose -p requesty -m anthropic/claude-sonnet-4-5 claude
```

Output shows:
- Which provider was selected
- Which ENV variables were set/removed
- The final `exec` command

## Stale model cache

If the provider's model list seems outdated:

```bash
leitum refresh --provider requesty
```

## Local Providers (Ollama, LM Studio, etc.)

### Token Counting Error (`count_tokens?beta=true`)

When launching Claude Code against a local provider, you might see an error/warning in the logs about:
```
GET /v1/messages/count_tokens?beta=true
```
Not all local servers implement this specific beta token-counting endpoint. This is usually **non-fatal**. Claude Code will continue to operate, although its internal token counting estimates might be slightly less precise or fall back to client-side heuristics.

### Model Does Not Support Tools

If Claude Code starts up successfully but fails when trying to read/write files or execute commands:
- **Cause**: The chosen local model does not support tool calling, or its tool calling capability is too weak.
- **Fix**: Switch to a model with strong tool calling capabilities, such as `qwen2.5-coder:14b` (or larger) or `llama3.1`.

### Context Window Limit Issues / Truncation

Local servers often default to small context limits (like 2K or 8K), which is insufficient for Claude Code's extensive prompts.
- **Symptom**: Claude Code cuts off mid-conversation, complains about reaching limits, or loses its memory of files it just read.
- **Fix**: Set a context limit of at least 32K (32768 tokens) - 64K (65536 tokens) is highly recommended.
  - For Ollama, the preset automatically configures `OLLAMA_CONTEXT_LENGTH: "32768"` via `extra_env`.
  - For LM Studio, adjust the context limit setting in the UI when loading the model.
  - For llama.cpp (`llama-server`), start with `-c 32768`.

### Connection Failures / "Server Not Running"

If `leitum doctor` or `leitum claude` complains that the local provider is unreachable:
- **Fix**: Make sure your local server is actually running and listening on the expected port (Ollama: `11434`, LM Studio: `1234`, llama.cpp: `8080`, vLLM: `8000`).
- **Versions**: Ensure your local tool is up to date:
  - **Ollama**: January 2026 release or newer (native Anthropic Messages API support).
  - **LM Studio**: version `0.4.1` or newer.

