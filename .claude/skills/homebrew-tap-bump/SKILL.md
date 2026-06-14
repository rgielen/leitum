---
name: homebrew-tap-bump
description: Bump the leitum Homebrew formula in rgielen/homebrew-taps after a new PyPI release, including regenerating transitive Python resource blocks when dependencies have shifted. Use when reviewing or merging an auto-generated bump PR, when the auto-bump warned that resources need updating, or when manually upgrading the formula without waiting for the workflow.
---

# Bump the leitum formula in `rgielen/homebrew-taps`

This skill ships the procedural knowledge that lives nowhere else in the
repo: the formula resides in a separate tap repository, and the
`dawidd6/action-homebrew-bump-formula` workflow only updates the main
formula `url` + `sha256` — it does not touch the 22+ resource blocks for
transitive Python dependencies. Whenever a Python dep version moves in
`uv.lock`, those resources need a human (or this skill) to regenerate them.

## When this skill applies

- A new `leitum` version was published to PyPI and the auto-bump PR
  appeared in `rgielen/homebrew-taps`, but it emitted the warning
  `This formula has resources that may need to be updated`.
- The user wants to bump the formula manually without waiting for the
  workflow (e.g. for a patch release tested locally).
- The auto-bump workflow failed and the formula must be updated by hand.

Do **not** use this skill for the very first publication of a new formula
or for unrelated tap maintenance — those need a wider scope than what is
encoded here.

## Locations

- Tap repository: `https://github.com/rgielen/homebrew-taps`
- Local working copy (expected): `~/DevHome/Projects/homebrew-taps/`
  (clone fresh from GitHub if missing — do not edit the brew-managed copy
  under `/opt/homebrew/Library/Taps/rgielen/homebrew-taps`)
- Formula: `Formula/leitum.rb`
- Tap name when invoking brew: `rgielen/taps` (Homebrew strips the
  `homebrew-` prefix)

## Procedure

### 1. Determine the target version and check for dep drift

```bash
cd ~/DevHome/Projects/leitum
LAST=$(git describe --tags --abbrev=0)   # previous release tag
NEW=v<X.Y.Z>                              # the version being bumped to
git diff "$LAST" "$NEW" -- uv.lock | grep -E "^\+name|^\+version" | head
```

If the diff shows no transitive-dep changes, you can merge the auto-bump
PR as is — the resources are still accurate. Skip to step 5.

If transitive deps moved, continue with step 2.

### 2. Capture the exact transitive dep set the new leitum will pull

Use a clean Python 3.11 or 3.12 venv. **Do not use Python 3.14** — the
`homebrew-pypi-poet` tool is broken there (removed `pkg_resources`), and a
fresh venv on 3.14 may also pull slightly different resolver results than
what end users will get.

```bash
rm -rf /tmp/leitum-deps-venv
python3.12 -m venv /tmp/leitum-deps-venv
/tmp/leitum-deps-venv/bin/pip install --quiet "leitum==<X.Y.Z>"
/tmp/leitum-deps-venv/bin/pip freeze | grep -v "^leitum==" > /tmp/leitum-deps.txt
```

### 3. Generate resource blocks from PyPI JSON

```bash
cat > /tmp/gen_resources.sh <<'EOF'
#!/bin/bash
set -euo pipefail
while IFS='=' read -r name _ version; do
  json=$(curl -sS "https://pypi.org/pypi/${name}/${version}/json")
  url=$(echo "$json" | jq -r '.urls[] | select(.packagetype=="sdist") | .url' | head -1)
  sha=$(echo "$json" | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256' | head -1)
  if [ -z "$url" ] || [ "$url" = "null" ]; then
    echo "WARNING: no sdist for ${name} ${version}" >&2
    continue
  fi
  # PEP 503 normalise: lowercase, replace _ and . with -
  norm=$(echo "$name" | tr '[:upper:]_.' '[:lower:]--')
  printf '  resource "%s" do\n    url "%s"\n    sha256 "%s"\n  end\n\n' "$norm" "$url" "$sha"
done < /tmp/leitum-deps.txt
EOF
bash /tmp/gen_resources.sh > /tmp/resources.txt 2> /tmp/resources.warn
cat /tmp/resources.warn   # must be empty; investigate any wheel-only deps
```

If `resources.warn` is non-empty, a dep has no sdist on PyPI. That is a
real blocker for source builds in Homebrew — escalate to the user.

### 4. Patch the formula

Open `~/DevHome/Projects/homebrew-taps/Formula/leitum.rb` and replace:

- `url` and `sha256` near the top with the new leitum sdist values
  (`curl -s https://pypi.org/pypi/leitum/<X.Y.Z>/json | jq '.urls[] | select(.packagetype=="sdist") | {url, digests}'`).
- Every resource block between `depends_on "python@3.13"` (more precisely:
  after the `maturin` resource) and `def install` with the contents of
  `/tmp/resources.txt`. Keep the `maturin` resource as-is unless you also
  intend to bump it.

**Invariants that must remain in the formula** — break them and the build
fails on `pydantic-core`:

- `depends_on "rust" => :build` (line must come before `depends_on
  "python@3.13"` to satisfy `brew audit --strict --new`).
- The `maturin` resource block is present and installed before the other
  resources.
- The `install` method installs `maturin` first, then the other resources,
  then `pydantic-core` with `build_isolation: false`, with
  `ENV.prepend_path "PATH", libexec/"bin"` set just before the
  pydantic-core install so the metadata-generation subprocess can exec
  `maturin`.

### 5. Verify locally before pushing

```bash
cd ~/DevHome/Projects/homebrew-taps
brew uninstall leitum 2>/dev/null
brew install --build-from-source rgielen/taps/leitum
brew audit --strict --new rgielen/taps/leitum
brew test rgielen/taps/leitum
leitum --version    # must match <X.Y.Z>
```

The Rust build of `pydantic-core` takes roughly 90 seconds on an M-series
Mac. If `brew install` fails mid-build, read
`~/Library/Logs/Homebrew/leitum/<N>.python3.13.log` for the actual
subprocess error — the brew summary alone is rarely informative.

### 6. Land the change

If the auto-bump opened a PR, push the resource fixes to that PR's branch
and merge. If you are bumping by hand, commit on `main` of
`rgielen/homebrew-taps` with a short message
(`leitum X.Y.Z`) and push.

Either way, do **not** ship a tap commit that has not been through `brew
install --build-from-source` plus `brew audit --strict --new` plus `brew
test` locally — there is no CI on the tap repo and end users will hit
build failures directly.

## After landing

A `brew update` on any end-user machine picks the change up automatically.
There is no PyPI-style propagation delay because the tap is read directly
from GitHub.

## When the auto-bump itself is broken

The auto-bump workflow is `.github/workflows/homebrew-bump.yml` in this
repo. It uses `dawidd6/action-homebrew-bump-formula@v6` with secret
`HOMEBREW_TAP_TOKEN` (fine-grained PAT, `contents:write` +
`pull-requests:write` on `rgielen/homebrew-taps` only). If the workflow
fails authentication, the secret has likely expired — regenerate the PAT
at `https://github.com/settings/personal-access-tokens` and update the
secret.

A no-op run (workflow triggered with the same tag the formula already
points to) intentionally exits non-zero. That is not a defect.
