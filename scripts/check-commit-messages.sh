#!/usr/bin/env bash
# Validates that every commit subject in a revision range is a Conventional
# Commit.
#
# leitum merges pull requests with a rebase strategy, so every individual commit
# lands on main, and python-semantic-release derives the version bump from these
# subjects. A mistyped type therefore produces a wrong release — or no release —
# without anything else going red.
#
# The type list mirrors python-semantic-release's commit_parser_options
# .allowed_tags. Keep the two in sync: a type accepted here but unknown to PSR
# parses as no bump at all.
set -euo pipefail

RANGE="${1:-origin/main..HEAD}"

PATTERN='^(feat|fix|perf|build|chore|ci|docs|style|refactor|test)(\([a-z0-9._/-]+\))?!?: .+'

subjects="$(git log --no-merges --format=%s "$RANGE")"
if [ -z "$subjects" ]; then
  echo "No non-merge commits in ${RANGE}; nothing to validate."
  exit 0
fi

failed=0
while IFS= read -r subject; do
  if printf '%s' "$subject" | grep -Eq "$PATTERN"; then
    printf 'ok    %s\n' "$subject"
  else
    printf 'FAIL  %s\n' "$subject"
    # GitHub Actions surfaces this in the job summary and the PR checks view.
    printf '::error::Not a Conventional Commit subject: %s\n' "$subject"
    failed=1
  fi
done <<< "$subjects"

if [ "$failed" -ne 0 ]; then
  cat >&2 <<'EOF'

Commit subjects must follow Conventional Commits:

    <type>[(scope)][!]: <description>

Allowed types: feat fix perf build chore ci docs style refactor test
A trailing "!" marks a breaking change, e.g. "feat!: drop Python 3.11".
EOF
  exit 1
fi
