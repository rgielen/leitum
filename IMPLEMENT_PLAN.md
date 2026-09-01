# Implementation plan — dependency and release automation

Implement this work by working its GitHub issues in `rgielen/leitum`.

The goal is a chain that needs no human hand: Renovate keeps dependencies
current and merges its PRs on green CI; a change that actually affects what
users receive is bumped, tagged and published automatically. Manual
intervention only when something fails.

1. List open issues assigned to you; pick the highest-priority one whose
   `Blocked by #N` references are all closed. `#28` and `#29` are unblocked and
   independent of each other, so they can run in parallel. The rest is a chain:
   `#30` needs `#28`; `#31` needs `#30`; `#32` and `#33` need `#31` and can then
   run in parallel.
2. Each issue carries a self-contained spec, but
   `prd/09-dependency-and-release-automation.md` is the source of truth — if the
   two disagree, the PRD wins, and the issue should be brought back in line.
3. Implement on a feature branch **in its own worktree**
   (`scripts/worktree-create.sh`, see the Git workflow section of `CLAUDE.md`).
   Commits, PR titles and PR bodies in English, Conventional Commits style.
   Merge with `gh pr merge --rebase`, then remove the worktree and the local
   branch from the primary checkout.
4. Before declaring an issue done, run `uv run ruff format --check src/ tests/`,
   `uv run ruff check src/ tests/`, `uv run mypy src/` and `uv run pytest`.
   State explicitly if any check was skipped and why.
5. Close the issue when its acceptance criteria are met, which unblocks its
   dependents.

## Two things a machine cannot do

- **Installing the Mend Renovate GitHub App** for `rgielen/leitum` is a manual
  step for the repository owner (`#32`). The `renovate.json` file is inert until
  it happens.
- **Proving the release chain end to end** requires a real `feat:`/`fix:` commit
  on `main`. Until one has gone through CI → semantic-release → PyPI →
  Homebrew PR, treat the chain as unproven, however green the workflows look.

## Constraints that are easy to violate silently

- `.github/workflows/release.yml` must keep its filename and its `name: Release`
  — PyPI trusted publishing is bound to the workflow filename.
- `platformAutomerge: false` in `renovate.json` is not optional: the repository
  has no branch protection, so GitHub's native auto-merge would merge PRs with
  failing checks.
- `release.yml` and `homebrew-bump.yml` must change in the same PR (`#31`);
  separately, `main` is broken in between.
