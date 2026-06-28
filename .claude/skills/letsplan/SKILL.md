---
name: letsplan
description: Structured planning workflow that turns a raw idea or feature request into refined requirements, an approved plan, PRDs (and ADRs when warranted), optional GitHub/GitLab issues with dependency ordering, and a clean implementation handoff. Use when the user wants to start a new application or service, or scope a substantial new feature, refactor, or migration — especially when they ask to plan, design, spec, architect, or write a PRD/ADR, or invoke /letsplan. Do NOT use for small localized changes (a single bug fix, a one-line edit, a trivial tweak); handle those directly.
---

# letsplan — from idea to implementation-ready plan

This skill drives a deliberate, gated path from a rough idea to artifacts that
can steer implementation in a *fresh* session or by independent subagents
without further human input:

1. Requirements — elicit, challenge, refine, research.
2. Plan — a precise, approved implementation plan.
3. PRDs (+ ADRs when a real architectural choice is made).
4. Optional issues / work items, or a local tracking decision.
5. Implementation handoff via `IMPLEMENT_PLAN.md`.

The artifacts *are* the state. Every decision is written to disk
(CLAUDE.md, PRDs, ADRs, IMPLEMENT_PLAN.md) as it is made, so the workflow
survives a `/clear` and can be resumed by re-reading those files.

## When this applies — and when it does not

Use it for greenfield apps/services and for substantial features, refactors,
or migrations of existing code.

Do **not** run the full process for small, localized changes (one bug, a tiny
tweak, a config flip). If a request is ambiguous in size, ask one triage
question (Phase 0) rather than assuming.

## Operating principles

- Favor simple, robust, legible solutions. Do not over-engineer small tasks;
  scale ceremony to the actual size and risk of the work.
- Challenge the input: check it for consistency, surface alternatives, and
  propose improvements for the user to decide on. You may always make
  suggestions — but the user decides.
- Research before asserting. For current versions, libraries, and best
  practices use **context7** (library docs) and **WebSearch** instead of
  relying on memory. Cite what you found when it changes a recommendation.
- Code-facing artifacts (code, comments, READMEs, commits, PRs) are English
  unless the project's CLAUDE.md says otherwise. The *artifact language* for
  PRDs/ADRs/issues is a separate, explicit decision (Phase 3).
- Confirm before irreversible or outward-facing steps (creating a remote repo,
  pushing, opening issues). Never write secrets/tokens into any artifact.

## Phase 0 — Triage and right-sizing

1. Classify the work: greenfield app/service, substantial feature/refactor, or
   small change. If small, say so and offer to skip the process and just do it.
2. State your understanding of the goal in one or two sentences and confirm it.
3. Check for a project CLAUDE.md. If none exists, create a minimal one (only
   what is needed: project purpose, stack, key conventions — no boilerplate).
   You will append decisions to it throughout.

Gate: get explicit confirmation that the full planning process is wanted before
proceeding.

## Phase 1 — Requirements, concept, architecture (in Plan Mode)

Run this phase in Claude Code **Plan Mode** so nothing is written until the plan
is approved.

1. Draft a concept for the user's requirements and ideas. Probe for missing
   constraints, edge cases, non-functional requirements, and assumptions.
2. Discuss options and trade-offs. Where the task warrants it (an application,
   a service architecture, a data model), examine the architectural
   constraints and propose an elaborated architecture. Keep proposals
   proportional — do not invent complexity a simpler design wouldn't need.
3. Research current techniques, versions, and best practices (context7,
   WebSearch) and fold findings into the proposal.
4. Ask whether accompanying documentation should be produced. If yes, and the
   answer is not already recorded in CLAUDE.md, ask for and record:
   - Format: **AsciiDoc** or **Markdown**.
   - Style and scope (depth, reference vs. guide, examples).
   - Audience and assumed prior knowledge.
   - Documentation language: **English** or **German**.
   Persist all of these in CLAUDE.md (see "CLAUDE.md decision block").

Gate: converge with the user on requirements and the architectural direction.

## Phase 2 — The plan

Produce a precise implementation plan: scope, the major work items, their
sequence and dependencies, the chosen architecture, risks, and a test
strategy. Present it for review via `ExitPlanMode`. Iterate until the user
approves. Approval here is the gate to writing PRDs/ADRs.

## Phase 3 — PRDs, ADRs, and repository setup

### 3a. Decide the artifact language (always make this decision)

The artifact language governs PRDs, ADRs, issues/work items, commit messages,
PR titles/bodies, and task descriptions. If CLAUDE.md already records it, reuse
it and say which. Otherwise ask explicitly — **English** or **German** — and
persist it. Never silently skip this decision.

### 3b. Decide where PRDs and ADRs live (ask per project)

Detect existing conventions and offer them as the default (e.g. a repo may
already use `prd/`). For greenfield, propose `docs/prds` and `docs/adrs`. Ask,
then persist the chosen paths in CLAUDE.md.

### 3c. Write the PRDs

Write one PRD per coherent area of work, into the chosen PRD folder. PRDs must
be precise and complete enough that, after a `/clear`, they alone can guide
implementation — explicit scope, acceptance criteria, data shapes, interfaces,
edge cases, and a test strategy. Number them for ordering (e.g. `00-overview`,
`01-…`). Include an **Implementation status** line in each PRD (initially
`planned`), to be updated as work completes.

### 3d. Write ADRs when (and only when) a real decision is made

Create an ADR for each significant, hard-to-reverse architectural choice
(framework, persistence, protocol, boundary). Skip ADRs for choices with an
obvious default. Use a lightweight MADR-style template:

```markdown
# NNNN. <short title of the decision>

- Status: accepted        # proposed | accepted | superseded by NNNN
- Date: YYYY-MM-DD

## Context
<the forces and constraints that make this a decision>

## Decision
<what we chose>

## Consequences
<positive and negative results, follow-ups, what this rules out>
```

Name files `NNNN-kebab-title.md` in the ADR folder. Ensure CLAUDE.md points to
the ADR folder so ADRs are discoverable (see decision block).

### 3e. Put the project under version control

If the directory is not a git repo, initialize it (sensible `.gitignore`,
first commit). Then offer to publish a remote, and walk the user fully through
setup using CLI tools when available:

- **GitHub** via `gh`: confirm auth (`gh auth status` / `gh auth login`), then
  `gh repo create` and push.
- **GitLab** via `glab`: ask for the instance base URL if self-hosted, confirm
  auth (`glab auth status` / `glab auth login --hostname <host>`), then
  `glab repo create` and push.
- **None**: keep it local.

Confirm before creating the remote or pushing — these are outward-facing.

### CLAUDE.md decision block

Maintain a single, idempotent section in the project's CLAUDE.md so decisions
survive `/clear`. Create or update it; do not clobber unrelated content:

```markdown
## Planning & documentation conventions (managed by /letsplan)

- Artifact language (PRDs, ADRs, issues, commits, PRs): <English|German>
- PRD location: <path>
- ADR location: <path>   # ADRs record architectural decisions; read before changing those areas
- Documentation: <yes/no> — format <AsciiDoc|Markdown>, language <English|German>,
  audience <...>, style/scope <...>
- Work tracking: <GitHub issues | GitLab issues | td-task-management | none>
```

## Phase 4 — Issues / work items, or local tracking

Ask whether issues / work items should be created in the remote (GitHub /
GitLab).

### If yes — issues drive implementation

Issues steer the work and hold its progress. Each issue correlates to a PRD and
is **self-contained**: embed a complete spec snapshot so an independent session
or subagent can implement it with no further input, **and** link the source PRD
file. The PRD remains the source of truth — if the two drift, the PRD wins and
the issue is brought back in line.

Issue body skeleton:

```markdown
## Goal
<one-paragraph outcome>

## Spec (self-contained snapshot of PRD <path>)
<everything an implementer needs: scope, acceptance criteria, interfaces,
edge cases, test strategy — copied so the issue stands alone>

## Source of truth
PRD: <path/in/repo>   # if this issue and the PRD disagree, the PRD wins

## Dependencies
Blocked-by: <#N, #M>  # see ordering note below
```

Encode ordering so independent sessions/subagents can compute sequence and
parallelism deterministically:

- **GitLab**: use native linked-issue relations ("blocks" / "is blocked by").
- **GitHub** (no native blocked-by): write `Blocked-by: #N` in the body and
  apply labels `ready` (no open blockers) vs. `blocked`. Optionally use
  sub-issues / task lists for parent-child structure.

Use `gh issue create` / `glab issue create`. Keep labels consistent so a
runner can pick the next unblocked, ready item.

### If no — local tracking

Propose the **td-task-management** skill for tracking the implementation across
sessions, and record the choice in CLAUDE.md (project level, not session
scope). In this mode the PRDs are the work list: each PRD's **Implementation
status** line is updated to `implemented` when its work is complete.

## Phase 5 — Implementation handoff

Write `IMPLEMENT_PLAN.md` at the repo root (committed) containing a prompt that
a fresh session or a new agent can run to implement the planned work. Pick the
variant matching the Phase 4 decision.

Issues-driven:

```markdown
# Implementation plan

Implement this project by working its issues in <GitHub|GitLab>.

1. List open issues; pick the highest-priority item that is `ready`
   (no open `Blocked-by`). Parallelizable items are those with disjoint,
   already-satisfied dependencies.
2. Each issue is self-contained, but treat the linked PRD as the source of
   truth if they disagree.
3. Implement, keeping commits/PRs in <artifact language>. Track progress in
   the issue; close it when its acceptance criteria are met and unblock
   dependents.
4. Repeat until no `ready` issues remain.
```

PRD-driven (local tracking):

```markdown
# Implementation plan

Implement this project from the PRDs in <PRD path>, in numeric order, honoring
stated dependencies.

1. Read <PRD path>/00-overview first, then each PRD in order.
2. Implement each PRD to its acceptance criteria; keep commits in
   <artifact language>.
3. When a PRD is fully implemented, set its Implementation status to
   `implemented`. Track work via td-task-management.
4. Stop and ask only when a PRD is genuinely ambiguous.
```

## Done criteria for a planning run

- Requirements and architecture agreed; plan approved.
- PRDs (and any ADRs) written in the chosen folders and language.
- CLAUDE.md decision block present and accurate; ADR folder discoverable.
- Repo under git; remote created if requested.
- Issues created (self-contained + PRD-linked, with dependency ordering) or a
  local-tracking decision recorded.
- `IMPLEMENT_PLAN.md` committed with the matching handoff prompt.
