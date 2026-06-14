# Getting Started

## Prerequisites

- Python 3.11 or newer
- [Claude Code](https://docs.claude.com/en/docs/claude-code/quickstart) installed and in your PATH
- An API key for your provider (e.g. Requesty)

## Step 1: Install leitum

```bash
pip install leitum
# or, without installation:
uvx leitum --version
```

## Step 2: Initialize

```bash
leitum init
```

This creates `~/.config/leitum/api-providers.yaml` with a commented example for Requesty.

## Step 3: Set your API key

```bash
export REQUESTY_API_KEY=your-key-here
# Add to ~/.zshrc or ~/.bashrc to persist
```

## Step 4: Launch Claude Code

```bash
leitum claude
```

leitum will prompt you to select a provider (if you have more than one) and models for each slot. Your choices are saved and pre-filled next time.

## Step 5: Verify with doctor

```bash
leitum doctor
```

A healthy output looks like:

```
--- Paths & Permissions ---
[ ok ] Config dir ~/.config/leitum has mode 0700
[ ok ] api-providers.yaml has mode 0o600

--- Config Validation ---
[ ok ] api-providers.yaml is valid (1 provider(s))

--- State File ---
[ ok ] state.yaml is valid

--- Environment Variables ---
[ ok ] Provider 'requesty': REQUESTY_API_KEY is set

--- Model Discovery ---
[ ok ] Provider 'requesty': 3 models from YAML

--- Claude Binary ---
[ ok ] 'claude' found at /usr/local/bin/claude
[ ok ] claude version: 1.x.x

--- Summary: 0 failure(s), 0 warning(s) ---
```
