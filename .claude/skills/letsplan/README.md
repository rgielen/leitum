# letsplan

A project-level Claude Code skill that drives a deliberate, gated path from a
rough idea to artifacts that can steer implementation in a *fresh* session — or
by independent subagents — without further human input.

`SKILL.md` holds the operational instructions Claude follows. This README
documents the skill for humans: what it does, when it fires, and why it is
shaped the way it is.

## What it produces

A full planning run leaves behind:

- A maintained **CLAUDE.md decision block** recording the conventions chosen
  for this project (artifact language, PRD/ADR locations, documentation
  settings, work-tracking choice).
- **PRDs** in the project's chosen folder, precise enough to guide
  implementation after a `/clear`, each carrying an *Implementation status*
  line.
- **ADRs** (MADR-style) for the architectural decisions that are actually hard
  to reverse — and only those.
- Optional **issues / work items** on GitHub or GitLab, or a recorded decision
  to track locally.
- An **`IMPLEMENT_PLAN.md`** at the repo root: a ready-to-run prompt that a new
  session or agent uses to implement the plan.

## When it activates

The skill is meant for greenfield applications/services and for substantial
features, refactors, or migrations of existing code.

- **Automatic:** Claude triggers it on its own only for larger undertakings —
  when the user wants to start a new app/service or scope a substantial change,
  or asks to plan, design, spec, architect, or write a PRD/ADR. Small, localized
  changes (a single bug fix, a one-line edit, a trivial tweak) deliberately do
  **not** trigger it.
- **Explicit:** invoke it with `/letsplan`. (A session restart may be needed
  before a newly added skill appears as a slash command.)

Phase 0 includes a triage question so that, when a request's size is ambiguous,
the skill confirms scope instead of running the heavy process by mistake.

## The five phases

| Phase | Purpose | Gate |
|------|---------|------|
| 0. Triage | Classify size, confirm the goal, ensure a minimal CLAUDE.md exists. | Confirm the full process is wanted. |
| 1. Requirements & architecture | Draft a concept, challenge it, research current practice (context7 / WebSearch), propose architecture, decide documentation settings. Runs in **Plan Mode**. | Converge on requirements and direction. |
| 2. Plan | A precise implementation plan presented via `ExitPlanMode`. | User approval. |
| 3. PRDs & ADRs | Decide artifact language and PRD/ADR folders, write PRDs (+ ADRs when warranted), put the repo under git, optionally create a remote. | Artifacts written and committed. |
| 4. Issues or local tracking | Create self-contained, PRD-linked issues with dependency ordering, or record a local-tracking decision (e.g. `td-task-management`). | Tracking method chosen. |
| 5. Handoff | Write `IMPLEMENT_PLAN.md` with the matching implementation prompt. | Handoff committed. |

Decisions are written to disk as they are made, so the workflow survives a
`/clear` and can be resumed by re-reading CLAUDE.md and the existing artifacts.

## Design decisions

These choices were made deliberately; change them in `SKILL.md` if your
workflow differs.

- **Scope guard over eagerness.** Auto-activation is restricted to larger
  undertakings, with a triage gate, so the process never gets in the way of
  small edits.
- **Plan Mode as the approval boundary.** Requirements and planning happen in
  Plan Mode; nothing is written until the plan is approved via `ExitPlanMode`.
- **PRD/ADR folders are asked per project.** The skill detects existing
  conventions (e.g. a repo already using `prd/`) and offers them as the
  default; greenfield defaults to `docs/prds` and `docs/adrs`. The choice is
  persisted in CLAUDE.md.
- **Artifact language is decided once, then reused.** The language for PRDs,
  ADRs, issues, commits, and PRs is recorded in CLAUDE.md; the skill reuses it
  on later runs instead of re-asking, but never skips the decision the first
  time.
- **Issues are self-contained snapshots that link the PRD; the PRD is the
  source of truth.** Each issue embeds a complete spec so an independent agent
  can work it with no further input, and links the originating PRD. If the two
  drift, the PRD wins and the issue is brought back in line. This keeps
  subagents autonomous without making issues the canonical spec.
- **Dependency ordering is explicit.** GitLab uses native blocked-by links;
  GitHub uses a `Blocked-by: #N` convention plus `ready` / `blocked` labels, so
  a runner can deterministically pick the next unblocked item and find
  parallelizable work.
- **ADRs only for real decisions.** MADR-style ADRs are written for
  hard-to-reverse architectural choices, not for choices with an obvious
  default.

## Files

```
.claude/skills/letsplan/
├── SKILL.md     # operational instructions Claude follows
└── README.md    # this document
```

## Notes

- This skill is generic. It lives at project level here, but its content does
  not depend on this project; copy it to `~/.claude/skills/letsplan/` to use it
  across all projects.
- The skill writes only planning artifacts and never records secrets or tokens.
  Remote creation and pushes are confirmed before they happen.
