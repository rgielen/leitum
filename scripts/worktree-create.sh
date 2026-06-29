#!/usr/bin/env bash
# WorktreeCreate hook for leitum.
#
# Claude Code calls this script INSTEAD of its built-in worktree creation
# whenever a worktree is requested (`claude --worktree` or a subagent launched
# with isolation: "worktree"). The contract is strict:
#
#   - the worktree-creation request arrives as JSON on stdin
#     (fields include at least `name`, sometimes `branch_name`, `cwd`, ...)
#   - this script must create the worktree itself
#   - it must print the absolute worktree path, and NOTHING else, on stdout
#   - any non-zero exit aborts worktree creation
#
# Therefore every diagnostic and every subprocess writes to stderr; only the
# final path goes to stdout. Optional setup steps (env copy, uv sync) are
# best-effort and must never fail creation.
set -euo pipefail

INPUT="$(cat)"

REPO_PATH="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

NAME="$(printf '%s' "$INPUT" | jq -r '.name // empty')"
[ -n "$NAME" ] || NAME="wt-$(date +%s)"
# Never let the name escape the worktrees directory.
NAME="$(printf '%s' "$NAME" | tr '/ ' '--' | tr -cd '[:alnum:]._-')"
[ -n "$NAME" ] || NAME="wt-$(date +%s)"

BRANCH="$(printf '%s' "$INPUT" | jq -r '.branch_name // empty')"
[ -n "$BRANCH" ] || BRANCH="leitum-wt-${NAME}"

WORKTREE_PATH="${REPO_PATH}/.claude/worktrees/${NAME}"

log() { echo "[worktree-create] $*" >&2; }
log "name=${NAME} branch=${BRANCH}"

mkdir -p "${REPO_PATH}/.claude/worktrees"

if git -C "$REPO_PATH" show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git -C "$REPO_PATH" worktree add "$WORKTREE_PATH" "$BRANCH" >&2
else
  git -C "$REPO_PATH" worktree add -b "$BRANCH" "$WORKTREE_PATH" HEAD >&2
fi

# Worktrees only contain git-tracked files. Copy local, gitignored files the
# worker needs (kept off stdout, never committed by the worker since they are
# gitignored).
for f in .env .env.local; do
  if [ -f "${REPO_PATH}/${f}" ]; then
    cp "${REPO_PATH}/${f}" "${WORKTREE_PATH}/${f}"
    log "copied ${f}"
  fi
done

log "running uv sync..."
( cd "$WORKTREE_PATH" && uv sync ) >&2 || log "uv sync failed (worker can retry)"

log "ready: ${WORKTREE_PATH}"
printf '%s\n' "$WORKTREE_PATH"
