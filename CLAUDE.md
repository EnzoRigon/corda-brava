# CLAUDE.md — working guide for Corda Brava

This file tells a Claude Code session how to work in this repo and how to **resume the build in a new session**. Read it first.

## What this is

**Corda Brava** — a themed tug-of-war party game (Inter vs Grêmio). The authoritative spec is **`prompt.md`** (leave it as-is). The build is executed task-by-task from a written plan, via subagents, with a per-task review gate. See `README.md` for the project overview and current status.

## Where the source of truth lives

- **Spec (what to build):** `prompt.md` — authoritative, do not edit.
- **Design decisions:** `docs/superpowers/specs/2026-11-03-corda-brava-design.md`.
- **Plan (task list):** `docs/superpowers/plans/2026-11-03-corda-brava.md` — 18 tasks, 4 phases (A backend core, B services+API+WS, C frontend, D docker+docs+e2e).
- **Progress ledger (READ THIS TO RESUME):** `docs/superpowers/sdd/2026-11-03-corda-brava/progress.md` — the authoritative record of what's done, every ruling made, and the exact next task + BASE commit. Per-task briefs and reports are in the same directory.

Trust the ledger + `git log` over memory. A task with a `Task N: complete` line is done — do not redo it.

## Current state (2026-11-04, session 2)

- **On `main`** (single branch, no worktree). All work merged and committed.
- **Phase A complete: Tasks 1–5 reviewed** (backend skeleton, pure game rules, SQLite repos, broker-shaped EventQueue, host auth). 78 backend tests passing at end of Phase A.
- **Phase B: Tasks 6–9 complete** (MatchService, ConsumerLoop, MatchRegistry, analytics, player API, pull ingest + /me). 116 tests passing; ruff + black clean.
- **Next task: Task 10 — host routes + WebSocket** (closes Phase B; carries several deferred minors, listed in the ledger). See the ledger for the downstream interfaces and deferred minors.

## How to build each task (the loop)

This project uses **subagent-driven development** (superpowers skill). For each task:

1. **Record BASE:** `git rev-parse HEAD`.
2. **Dispatch one implementer subagent** on model **`sonnet`** (see model note below) with: the task brief path (`docs/superpowers/sdd/.../task-N-brief.md` — regenerate with the SDD `task-brief` script if needed), the interfaces/signatures it depends on from earlier tasks' reports, and the global constraints. The implementer does TDD, runs `cd backend && python -m pytest`, lints, commits, and writes a report file. It must NOT dispatch subagents and must NOT touch git branches/merges.
3. **Review:** build a diff package (SDD `review-package` script, BASE..HEAD) and dispatch a reviewer subagent (also `sonnet`) that reads brief + report + diff and returns Spec ✅/❌ + findings.
4. **Fix loop** (max 5 rounds): resume the implementer with any Critical/Important findings; re-review the fix diff. Minors are deferred and noted in the ledger.
5. **Record completion** in the ledger (`Task N: complete (commits base..head, review clean)`), then move on.

Do NOT implement or fix code yourself in the controller session — dispatch subagents. The controller only coordinates, reviews packaging, and updates the ledger.

### Model note (important for this environment)

Spawned subagents inherit a large MCP/tool-definition payload (~300k tokens). **Haiku (200k context) cannot hold it and will fail** with "Prompt is too long". Use **`sonnet`** (the configured Sonnet is a 1M-context variant) for every subagent — implementers and reviewers. Use the most capable model (`opus`) only for the final whole-branch review.

## Keeping progress & docs updated (do this as you go)

- After each task: append the result + any **rulings** to `docs/superpowers/sdd/2026-11-03-corda-brava/progress.md`, and copy the task's brief/report into that same tracked `docs/superpowers/sdd/...` directory (the live SDD scratch under `.superpowers/` is git-ignored and will NOT survive to a new session — only the `docs/` copies are versioned).
- Update `README.md`'s status table when a task or phase completes.
- Commit the docs together with (or right after) the task code so the ledger on `main` always reflects reality.

## Git / workflow conventions

- Work on `main`. Commit per task with conventional-commit messages (`feat(...)`, `fix(...)`, `chore(...)`).
- Remote: `https://github.com/PauloDalsoto/corda-brava` (push `main`).
- `.gitignore` already excludes `.DS_Store`, Python `.venv`/caches, `*.db`, node_modules, and `.claude/worktrees/`.
- The backend `.venv` is git-ignored — recreate it per the README when running tests.

## Art & assets policy (must hold)

The mascots (Saci / Mosqueteiro) and club crests are **owner-authored image files** committed under `docs/`. The app only **copies and displays** them — **no code may draw, generate, or render the club mascots or crests**. If new art is needed, use original assets/characters, never code that reproduces the club characters.

## Conventions from the spec worth remembering

- Player-facing text is **PT-BR**; code/comments English.
- Rope: `[-ROPE_TARGET, +ROPE_TARGET]`, 0 center, negative = Inter (left), positive = Grêmio (right).
- Scoring default `normalized`; server-authoritative timer; one player per device; late-join blocked by default.
- Queue contract is broker-shaped (async/leased/ack/idempotent-by-batchId) so the consumer is swap-ready for Azure Service Bus with no changes.
