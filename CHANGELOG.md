# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1.0] - 2026-06-14

### Added
- `leitum claude` — launch Claude Code via a configured provider
- Provider configuration in `~/.config/leitum/api-providers.yaml`
- Interactive provider and model selection with `questionary`
- State persistence to `~/.local/state/leitum/state.yaml`
- Project-local config via `leitum.yaml`
- Model discovery via API with 24-hour cache
- `leitum init` — initialize config
- `leitum provider list/show/add/remove` — manage providers
- `leitum refresh` — refresh model cache
- `leitum doctor` — sanity check suite
- `leitum completions` — shell completion scripts
- `--dry-run` and `--verbose` flags
- Full test suite (unit + integration)
- CI via GitHub Actions (Python 3.11–3.13, macOS + Linux)
