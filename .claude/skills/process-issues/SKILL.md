---
name: process-issues
argument-hint: "[key=value ...]  e.g.  max_parallel=8 worker_model=opus label=ready"
description: Process open GitHub issues assigned to the current user into review-ready Pull Requests. Selects eligible issues, orders them by dependency (text refs like "Depends on #N" plus GitHub-native relations) and otherwise first-come-first-serve, then dispatches up to four parallel worker subagents — each in its own git worktree with a clean context — that implement the issue per its spec and open a draft PR. Use when the user wants to auto-work the issue backlog, batch-implement assigned issues, or invoke /process-issues. Never merges; every issue results in a PR for human review.
---

# Process assigned issues into review-ready PRs

You are the **orchestrator**. You do NOT implement issues yourself. Your job is
to select eligible issues, enforce dependency ordering, and dispatch one
isolated worker per issue. Each worker runs in its own git worktree with a clean
context and opens a Pull Request for human review.

## When this applies

- The user wants the open issue backlog worked automatically.
- Only issues **assigned to the current user** are in scope (`--assignee @me`).

Do NOT use this to merge anything, to triage/label-cleanup, or to work issues
that are not assigned to the current user.

## Prerequisites (already configured in this repo)

- Labels `in-progress` (claim) and `needs-spec` (parked) exist.
- `.claude/settings.json` registers a `WorktreeCreate` hook
  (`scripts/worktree-create.sh`) that creates each worker's worktree, copies
  `.env`/`.env.local` into it, and runs `uv sync`. Workers therefore start ready
  to run the quality gates.
- `gh` is authenticated. Verify with `gh auth status` if anything fails.
- **The orchestrator session runs in an autonomous permission mode (Auto Mode).**
  Background workers inherit the parent session's permission mode and cannot
  answer interactive prompts, so without it they stall. Enable Auto Mode before
  running this skill — either `permissions.defaultMode: "auto"` in
  `.claude/settings.local.json`, launching with `--permission-mode auto`, or
  Shift+Tab to "auto" in the session. An agent cannot enable this for itself;
  the user must set it. If a worker hangs without progress, Auto Mode is off.

If a label is missing: `gh label create in-progress` / `gh label create needs-spec`.

## Parameters

- `ASSIGNEE`: `@me`
- `MAX_PARALLEL`: `4`
- `WORKER_MODEL`: `sonnet`
- `CLAIM_LABEL`: `in-progress`
- `BLOCK_LABEL`: `needs-spec`
- `BASE_BRANCH`: `main`

### Overrides at invocation

The invocation arguments are: `$ARGUMENTS`

Parse them as space-separated `key=value` pairs and override the defaults above;
keys are case-insensitive and match the parameter names (`max_parallel`,
`worker_model`, `assignee`, `claim_label`, `block_label`, `base_branch`, plus
`label=<name>` to additionally restrict the scope to issues carrying that
label). Any parameter not given keeps its default. If `$ARGUMENTS` is empty, use
all defaults. Reject unknown keys with a one-line note instead of guessing.

Examples:
- `/process-issues` — all defaults (4 workers, Sonnet, assigned to me)
- `/process-issues max_parallel=8`
- `/process-issues max_parallel=2 worker_model=opus label=ready`

## Procedure

### 1. Discover candidates

```
gh issue list --assignee @me --state open \
  --json number,title,body,labels,createdAt,url --limit 200
```

Drop any issue that already carries `CLAIM_LABEL`, `BLOCK_LABEL`, or already has
an open linked PR.

### 2. Build the dependency graph

For each candidate, collect dependencies from BOTH sources:

- **Text refs** in title/body (case-insensitive): `depends on #N`,
  `blocked by #N`, `needs #N`, `after #N`.
- **GitHub-native relations**: query sub-issue and "blocked by" links via
  `gh api` (try GraphQL first). If a field/endpoint is unavailable in this repo,
  degrade gracefully to text refs only — do not fail the run.

A dependency is **satisfied only when the referenced issue is CLOSED**. Because
PRs are reviewed by a human and never auto-merged, dependent issues normally
wait for a later run, after their blocker's PR has been merged. This is expected.

Detect cycles; skip issues inside a cycle and report them.

`READY` = a candidate whose every dependency is satisfied.

### 3. Order the READY set

First-Come-First-Serve: oldest `createdAt` first.

### 4. Spec gate (cheap, before dispatch)

Read each READY issue. If the spec is not actionable (no clear acceptance
criteria / ambiguous scope), do NOT build it: post a short clarifying comment,
add `BLOCK_LABEL`, and skip. Only dispatch issues with an actionable spec.

### 5. Dispatch loop (at most MAX_PARALLEL in flight)

For each READY + actionable issue, keeping at most `MAX_PARALLEL` running:

1. Re-check it is still unclaimed, then claim it:
   `gh issue edit <N> --add-label "in-progress"`
2. Launch a **worker** as a background subagent with worktree isolation and a
   clean context — use the Agent/Task tool with `subagent_type: "general-purpose"`,
   `model: "<WORKER_MODEL>"` (default `sonnet`; subagents do not reliably inherit
   the parent model, so set it explicitly), `isolation: "worktree"`, and
   `run_in_background: true`. Pass the Worker Prompt below, filled in with this
   issue's number, title, and body.

When a worker finishes, free its slot and dispatch the next READY issue. Repeat
until no READY issues remain.

### 6. Per-issue outcome

- **Success** (PR opened): comment the PR link on the issue; remove `CLAIM_LABEL`.
- **Failure**: remove `CLAIM_LABEL`, comment a one-paragraph failure summary,
  move on. Never leave an issue half-claimed.

### 7. Final report

Print a table: issue → PR url / `skipped (needs-spec)` / `failed` /
`waiting on #N`.

## Worker Prompt (fill in per issue, pass to each subagent)

```
You are implementing ONE GitHub issue in an isolated git worktree. You have a
clean context and your own checkout — assume no prior conversation.

Issue #<N>: <title>
Spec:
<body>

Rules:
1. Read this repo's CLAUDE.md and obey it. Implement strictly per the spec. If
   something is genuinely underspecified, make the minimal reasonable choice and
   record it under "Open questions" in the PR body — do NOT expand scope.
2. Create a fresh branch off main: feat/issue-<N>-<short-slug>.
3. The worktree is already bootstrapped (deps synced, .env present). If a
   dependency is missing, run `uv sync`.
4. Quality gates — all must pass before opening the PR:
     ruff format  &&  ruff check  &&  mypy --strict  &&  pytest
   If you cannot make them pass, STOP and report — do not open a broken PR.
5. ALWAYS open a Pull Request for human review. Never merge and never push to
   main. Conventional-Commits title, English body with a short summary and a
   test-plan checklist, and "Closes #<N>". Open it as a draft.
6. Do not touch other issues, branches, or unrelated files.

Return: the PR URL, or a clear reason if you stopped without a PR.
```

## Notes

- **Worker model.** Workers run on `WORKER_MODEL` (default `sonnet`) regardless
  of the orchestrator's model. To change it for a run, override the parameter.
- **Parallel cap.** Four workers is the practical sweet spot; review throughput,
  not Claude, is the bottleneck above that. Each worker is an independent
  context, so N workers cost up to N times the tokens.
- **Isolation.** The `WorktreeCreate` hook copies gitignored files (`.env`) into
  each worktree. Those files are gitignored, so a worker cannot commit them.
- **Idempotency.** Re-running the orchestrator is safe: claimed (`in-progress`)
  and parked (`needs-spec`) issues, and issues with an open PR, are skipped.
- **Post-merge cleanup.** Each worker leaves a `feat/issue-<N>` branch plus an
  agent worktree under `.claude/worktrees/`. The orchestrator never merges, so
  these persist until a human merges the PR. The remote branch is auto-deleted
  on merge (`delete_branch_on_merge`); the local worktree and branch must be
  removed afterwards from the primary checkout — see CLAUDE.md "Git workflow"
  for the exact procedure. Do not run the merge/cleanup from inside the worktree.
