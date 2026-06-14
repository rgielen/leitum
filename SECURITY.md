# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities by opening a GitHub issue with the label "security",
or by emailing the maintainer directly.

Do not include API keys, tokens, or other secrets in any report.

## Token Handling

leitum reads API tokens from environment variables and writes them only to
`~/.config/leitum/api-providers.yaml` (mode 0600). Tokens are never written
to logs, stdout, or files outside this location.

Use `${VAR}` interpolation in config files instead of inline secrets:

```yaml
auth:
  token: ${MY_API_KEY}   # good
  # token: sk-actual-key   # never do this
```
