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
