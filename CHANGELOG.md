# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1.2] - 2026-07-03

### Added
- `process-issues` project skill: parallel issue-to-PR workflow that dispatches
  up to 4 worktree-isolated Claude Code subagents for assigned open GitHub issues
  and opens each resulting PR ready for review.
- `homebrew-tap-bump` project skill: bumps the Homebrew formula in
  `rgielen/homebrew-taps` after a new PyPI release, including regenerating
  transitive Python resource blocks.
- `letsplan` project skill: structured planning workflow that turns a raw idea
  into refined requirements, an approved plan, and optional GitHub issues.
- `key=value` parameter overrides for the `process-issues` skill invocation.

### Fixed
- `api-providers.yaml` is now written atomically (temp-file + rename) to prevent
  partial writes on `provider add` / `provider remove`.
- `save_state` no longer attempts a double `os.close()` on the temp file
  descriptor when the atomic write fails.
- `--use-last-provider` / `--use-last-model` now fall through to the project
  config when the state file has no saved value for the respective field.
- `--dry-run` is now fully side-effect-free: state and model-cache writes are
  skipped.
- Config file initialization is hardened against race conditions when multiple
  leitum processes start simultaneously.
- `process-issues` skill: improved error message when `jq` is not installed.

### Changed
- `.env` and Claude Code worktree directories (`.claude/worktrees/`) are
  added to `.gitignore`.
- Homebrew install instructions now point to `rgielen/taps`; formula is
  auto-bumped on each PyPI release via a GitHub Actions workflow.
- Git workflow documentation tightened: no automatic squash-merges; local
  branch/worktree cleanup is always required after a PR merge.

## [0.1.1] - 2026-06-14

### Fixed
- `leitum --dry-run claude` no longer requires the `claude` binary to be present
  in `PATH`. The check now runs only when leitum is about to `exec` claude.

### Changed
- GitHub Release assets are restricted to wheel, sdist, and Sigstore
  attestation files (no longer picks up `dist/.gitignore`).

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
