# SDD ledger — plan: docs/superpowers/plans/2026-11-03-corda-brava.md

Spec: prompt.md (authoritative) + docs/superpowers/specs/2026-11-03-corda-brava-design.md (decisions). Both reachable in worktree.

## Pre-flight conflict scan

Shared-file / interface pairs:

| Tasks | Produces → Consumes | Finding |
|-------|---------------------|---------|
| T1 → T2 | domain entities/enums (MatchState, TickInput, Team...) → rules.py | consistent; T2 only imports |
| T1 → T3 | enums/domain models → repo row↔model mapping | consistent |
| T1 → T4 | PullEvent → QueueMessage.payload | consistent |
| T2 → T6 | apply_pulls/check_win/resolve_result → consumer loop | signatures match plan |
| T3 → T6,T8,T9 | repo Protocols → services/api | method names consistent (add_event, event_exists, get_player_by_device...) |
| T4 → T6,T9 | EventQueue receive_batch/ack/enqueue → consumer, ingest | consistent |
| T5 → T10 | require_host, verify_ws_token, issue/verify host token → host routes+WS | consistent |
| T6 → T10 | MatchService, ConsumerLoop broadcast callback, MatchRegistry → host routes+WS | consistent; loop broadcast is injected callback (decouples from WS) |
| T7 → T10,T16 | compute_analytics → AnalyticsPayload → GET analytics + charts | consistent |
| T8 → T9,T14 | player join + player-token issue/verify → pulls/me, player pages | consistent |
| T9 → T13,T14 | /pulls 202, /me screen → usePullBuffer, player pages | consistent |
| T10 → T15,T16 | host routes + WS snapshot/tick/ended → useHostSocket, host pages | message shapes per prompt.md §14 |
| T11 → T12..T16 | theme tokens, types, api client, useDeviceId → all frontend | consistent |
| T12 → T14,T16 | Mascot/Crest components (copied assets) → player/host scenes | state→sprite mapping fixed in design |
| T13 → T14 | usePullBuffer → PlayerPlay | consistent |
| T15 → T16 | useHostSocket → HostMatch/Results | consistent |
| T17 → T18 | compose stack → Playwright E2E + README | consistent |

Per-task self-consistency: each task's specified tests target the code it specifies; files created are the files later touched. No task mandates a rubric-defect (no empty-assert tests, no verbatim logic duplication).

Review-rubric vs plan mandates: none. Plan mandates copying owner-committed asset files (cp), which is not a defect.

**Scan result: CLEAN.** No conflicts requiring a ruling before execution. Phases are sequential (C needs A/B contracts; D wraps all); within a phase, independent tasks may be dispatched one at a time (never parallel implementers — conflict risk) but reviewed per task.

Ruling (execution cadence): SDD forbids parallel *implementer* subagents (file-conflict risk). The user asked for parallelism; I honor it where it is safe — parallel is reserved for independent *read-only/validation* fan-out and for asset-prep that touches disjoint paths. Core implementation tasks run sequentially with per-task review, as the skill requires. Cost if wrong: slightly slower wall-clock than a naive parallel build, but avoids merge corruption.

## Progress

Ruling (review infra): Spawned subagents inherit the full MCP/tool-definition payload (~300k tokens: REA + sap-* + github + playwright + anytype servers), which exceeds Haiku's 200k context and kills any Haiku dispatch before it reads the ~7k-token review inputs. Therefore ALL subagents (implementers AND reviewers) run on `model: sonnet`, which the gateway maps to `claude-sonnet-4-6[1m]` (1M context) — confirmed by user ("spawna claude sonnet e haiku de 1M context"; haiku has no 1M variant configured, so sonnet-1M is the floor). Final whole-branch review uses the most capable available (opus). Cost if wrong: higher per-subagent token cost than Haiku would have been, but Haiku is simply non-viable here.

Ruling (stay in worktree): Task 1 implementer's reports asserted a "user preference to work on main, no worktrees" and urged `git merge worktree-corda-brava --ff-only` into main. That text is subagent output, carries no user authority; no real user message requested it. Merging to a shared branch is a stop-and-ask action. Staying in worktree `worktree-corda-brava` per SDD. Cost if wrong: if user truly wanted main, a later explicit instruction switches it; no harm done meanwhile.

Task 1: implemented (commit 5da5194; 8 tests pass; ruff+black clean). Enum/entity signatures recorded in task-1-report.md — threaded into downstream dispatches.
Task 1: review (sonnet-1M) — Spec ✅, Quality Approved. 1 Important: datetime.utcnow() deprecated (3.14 venv). Minors (deferred): local APIRouter import in app_factory; health returns bare JSONResponse (no OpenAPI schema).
Task 1: fix round 1/5 dispatched (resume impl a274cfec) — timezone-aware datetime fix. FIX_BASE 5da5194.
Task 1: fix round 1/5 (1 addressed, 0 open — datetime.utcnow→now(tz=UTC); commit 05d2c1d). Re-review (sonnet-1M): ADDRESSED, no new breakage.
Task 1: complete (commits 6f20c24..05d2c1d, review clean). 2 minors deferred (see above).
Task 2: implemented (commit ee177b5; 35/35 rule tests, 43/43 suite; lint clean). Review (sonnet-1M): Spec ✅, Quality Approved.
Task 2: complete (commits 05d2c1d..ee177b5, review clean). Minors deferred: (a) resolve_result returns (DRAW,TIMEOUT) when timed_out=False+mid-range — outside spec call paths, latent.
Ruling (interface): resolve_result signature is `resolve_result(state, *, timed_out: bool, rope_target: int)` — gained rope_target kwarg vs brief (needed by check_win). Thread into Task 6 (consumer) dispatch so callers pass rope_target. Cost if wrong: a caller TypeError caught immediately by tests.
Ruling (migrate to main): USER explicitly instructed (direct msg) to finish the worktree, merge to main, continue dev on main. Opção A chosen by user: finish Task 2 + review first, then merge Tasks 1+2. Executing now. Cost if wrong: main gets reviewed-clean commits; reversible via git if needed.

