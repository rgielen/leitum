# leitum Roadmap

This document outlines the planned and completed features for `leitum`.

## Shipped Features (v1)

### Local Providers Manual Integration
- **Manual Configuration Guidance**: Step-by-step setup guides for popular local, Anthropic-compatible servers: Ollama, LM Studio, llama.cpp, and vLLM. See [Ollama](providers/ollama.md), [LM Studio](providers/lm-studio.md), and [Local Providers](providers/local.md) documentation.
- **Context handling**: Recommended context lengths are documented for local providers.

---

## Planned Features (v1 & beyond)

### Local Provider Automation (In Progress)
- **Interactive presets** for local servers: Ollama, LM Studio, llama.cpp, and vLLM to easily configure them without prompts.
- **Automatic detection** (`leitum provider detect`): Scan local ports to discover running instances of local servers and configure them with one click.

### Extra Providers & Presets
- Preset wizards for more remote API routing/proxy options (OpenRouter, LiteLLM, etc.).

### Security
- **macOS Keychain Integration**: Encrypted, system-native storage of API tokens/keys instead of raw config files.

### Configuration & Contexts
- **Named profiles / contexts** (kubectl-style): Seamlessly switch between different environments, accounts, or sets of providers.

### Agent Support
- Support for other terminal-based agents beyond Claude Code: `leitum copilot`, `leitum opencode`, etc.

### Distribution
- **Homebrew Core**: Submit the `leitum` recipe directly to Homebrew Core.
