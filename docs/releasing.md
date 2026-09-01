# Releasing and dependency updates

This page is for contributors. Releases of `leitum` are automatic: nobody bumps
a version, edits the changelog, or pushes a tag by hand. What you write in a
commit message decides whether a release happens.

The authoritative specification is
[`prd/09-dependency-and-release-automation.md`](../prd/09-dependency-and-release-automation.md).

## The chain

```
pull request ──→ CI ──→ rebase merge into main
                                │
main ──→ CI ──→ green ──→ Release workflow
                          ├─ feat:/fix:/perf: since the last tag
                          │    → version + CHANGELOG.md + uv.lock
                          │    → commit, tag, GitHub release
                          │    → PyPI (trusted publishing) → Homebrew tap PR
                          └─ nothing releasable → green, no release
```

Everything runs in one workflow. A release that stops halfway is a failed
workflow run, not a silent partial publish.

## What triggers a release

The commit type decides. Types follow
[Conventional Commits](https://www.conventionalcommits.org/) and are validated
on every pull request by the `Conventional Commits` CI job.

| Commit type | Effect |
|---|---|
| `feat:` | minor release (0.1.6 → 0.2.0) |
| `fix:`, `perf:` | patch release (0.1.6 → 0.1.7) |
| `feat!:` and other breaking changes | minor release, **not** major |
| `docs:`, `test:`, `refactor:`, `chore:`, `ci:`, `build:`, `style:` | no release |

Breaking changes bump the minor because the project is deliberately pre-1.0
while the public interface is still moving. It will not jump to 1.0.0 by
accident.

Nothing is lost by not releasing. Non-releasing commits accumulate on `main` and
ship with the next `feat:` or `fix:`, and they all appear in that release's
changelog section.

Write commit messages as if they were the changelog, because they are.

## Dependency updates

[Renovate](https://docs.renovatebot.com/) keeps dependencies current. Its pull
requests run the full CI matrix and are merged by rebase when green. They do
**not** produce a release, and that is deliberate.

`pyproject.toml` declares open lower bounds (`httpx>=0.27` and so on), so a
newer version still satisfies the range and Renovate only rewrites `uv.lock`.
That file is not packaged into the sdist or wheel — the artifact's dependency
metadata is the ranges — and the Homebrew formula builds its `resource` blocks
from the pip resolution of the published sdist. A release for such an update
would be bit-identical to the one before it.

So for `leitum`, `uv.lock` is an early-warning instrument: CI continuously
proves the project still builds, tests and type-checks against the newest
versions of its dependencies.

**Security advisories are the exception.** There Renovate raises the lower bound
in `pyproject.toml` and commits it as `fix(deps): …`. That genuinely changes what
users install, so it releases like any other fix.

Two things are exempt from automatic merging:

- Updates to `video/`, the Remotion project behind the README demo. CI does not
  build it, so a green run says nothing about them. Those pull requests wait for
  a human.
- Anything whose CI run is red. The pull request simply stays open.

## When something goes wrong

- **A Renovate pull request is red.** Look at it. Either the dependency broke
  something (fix it, or pin the dependency) or the update is fine and a test
  needs adjusting.
- **The Release workflow failed.** Nothing was published. Read the run, fix the
  cause, and push again — the next green CI run on `main` retries the whole
  decision from scratch.
- **A release happened but the Homebrew pull request looks wrong.** The tap has
  no CI. Verify locally before merging:

  ```bash
  brew install --build-from-source rgielen/taps/leitum
  brew audit --strict rgielen/taps/leitum
  brew test rgielen/taps/leitum
  ```

  Only the formula's `url` and `sha256` are bumped automatically. If a release
  changed the transitive dependency set, the `resource` blocks need regenerating
  first.

- **A release is needed right now and no releasable commit exists.** Land the
  actual fix as `fix:`. Do not push a tag by hand; a hand-made tag is not what
  the chain publishes from and will only cause drift.
