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

## MIGRATION TO MAIN (done)
- Exited worktree (kept). Back in main checkout /Users/pauloricardodalsoto/orca/projects/trabGb.
- main had diverged: commit 2ad7371 added docs/, prompt.md, .claude/skills/pixel-art-studio/ (the sprite-gen work that produced the owner's mascot gifs/pngs). NO backend files → disjoint from worktree branch.
- Merged worktree-corda-brava into main (merge commit f076ea0, no conflicts). Backend Tasks 1+2 now on main.
- Versioned SDD scratch (ledger/briefs/reports/diffs) into tracked docs/superpowers/sdd/2026-11-03-corda-brava/ + added .gitignore + untracked .DS_Store (commit 2e109e8). User can resume in another session from these tracked files.
- Verified: backend source intact on main; python3 3.14.2 available; .venv is gitignored (subagents recreate per task).
- ALL FURTHER WORK HAPPENS ON main (no more worktree). Dispatch cwd = /Users/pauloricardodalsoto/orca/projects/trabGb. Live ledger = THIS tracked file (docs/superpowers/sdd/...). Keep it updated and it is auto-versioned on next commit.

NEXT: Task 3 (repositories + SQLite). BASE for Task 3 = current HEAD 2e109e8.

## Worktree removed (user instruction)
Worktree + branch worktree-corda-brava fully merged into main, then removed (git worktree remove --force + branch -d + prune). Single branch main @ 2e109e8 at that point. All work on main henceforth.

Task 3: implemented (commit e09ec88; 60 pass [17 new repo + 43 prior]; lint clean). Review (sonnet-1M): Spec ✅, Quality Approved. UniqueConstraintError wraps sqlite IntegrityError (player_repo); add_event uses INSERT OR IGNORE (dedup, no crash); WAL + module threading.Lock write_lock; datetimes isoformat/fromisoformat tz-aware UTC; enums stored as .value. Minors deferred: (a) write_lock() annotated -> object not Generator; (b) bootstrap_db returns raw sqlite3.Connection (infra, tests discard it).
Task 3: complete (commits 2e109e8..e09ec88, review clean).

NEXT: Task 4 (EventQueue broker-shaped + in-memory lease/ack/redelivery). BASE = e09ec88. Then Task 5 (host auth). Both depend only on Task 1 entities (PullEvent). Sequential (no parallel implementers per SDD).

Task 4: implemented (commit 5578afc; 71 pass [60 prior + 11 queue]; lint clean). Review (sonnet-1M): Spec ✅, Quality Approved. Genuine broker semantics: receive_batch leases into _inflight with expires_at; _reclaim_expired_leases inside receive_batch moves expired back to _pending with delivery_count+1; ack pops permanently; abandon releases early (no count bump); factory memory→InMemoryEventQueue, azure_service_bus→NotImplementedError naming AzureServiceBusEventQueue. Redelivery test load-bearing confirmed (lease 0.05s, no ack, re-receive delivery_count>=2). Constructor injectable: lease_timeout_s, time_fn. Important (deferred): receive_batch polls ~100Hz when empty (future: asyncio.Event). Minors (deferred): abandon count diverges from Azure native (adapter will match); factory unknown-backend ValueError untested.
Task 4: complete (commits e09ec88..5578afc, review clean).

## Phase A status: Tasks 1,2,3,4 COMPLETE & on main. Task 5 (host auth) still pending.
## HEAD after Task 4 = 5578afc. BASE for Task 5 = 5578afc.

## END-OF-DAY (user plan): finish today, resume tomorrow in a NEW session.
User instructions for wrap-up: (1) create root CLAUDE.md + README.md explaining repo/project/how-to-proceed/how-to-keep-progress-and-docs-updated; (2) commit everything; (3) push WHOLE repo to https://github.com/PauloDalsoto/corda-brava (awaiting user confirm: repo already created? push only main?).
Asset policy to document: NO code draws/renders the club mascots or crests; the one asset step only copies owner-authored committed image files and displays them.


## SESSION 2 (2026-11-04) — resumed on Windows
Env: repo cloned to C:\Users\Paulo\OneDrive\Área de Trabalho\corda-brava; backend .venv recreated (Python 3.12.2, Windows -> `.venv/Scripts/python`). Baseline 71 pass.

Task 5: implemented (commit 8e75e62; report 2e9a61c; 78 pass [71 prior + 7 new]; ruff+black clean). host_session.py: check_password (compare_digest on bytes), issue_host_token(settings)->(token, expires_at) HS256 role=host, verify_host_token never raises. api/auth.py: require_host (Bearer via get_settings dep -> 401 + WWW-Authenticate: Bearer), verify_ws_token(token: str | None, settings)->bool (caller closes WS 1008 in Task 10). schemas/host.py: HostLoginRequest{password}, HostLoginResponse{token, expiresAt}. Login ROUTE deferred to Task 10 per plan.
Task 5: review (sonnet-1M) — Spec ✅, Quality Approved. Minors deferred: (a) jwt.decode should pass options={"require": ["exp"]} + test token-without-exp rejected; (b) no test pins algorithm (alg=none / HS512 rejected); (c) 1 pytest warning untraced (possibly PyJWT short-HMAC-key warning in tests).
Task 5: complete (commits 3e1790c..8e75e62, review clean).

## Phase A COMPLETE (Tasks 1-5). HEAD after Task 5 docs = see git log. NEXT: Task 6 (MatchService + ConsumerLoop + MatchRegistry). Thread into Task 6 dispatch: resolve_result(state, *, timed_out, rope_target) kwarg; queue API receive_batch/ack/abandon (task-4-report); repos (task-3-report).

Task 6: implemented (commit 2b366c7; report 803d9d5; 86 pass). Review (sonnet-1M): Spec ✅, Changes requested — 4 Important: (1) poison message (unknown player FK) killed loop, match stuck RUNNING; (2) loop task exceptions never logged, stop_loop swallowed caller CancelledError; (3) dedup "persisted" vs "applied" hole lost rope delta on mid-tick failure; (4) abandoning foreign-match messages -> head-of-line blocking / delivery_count inflation.
Task 6: fix round 1/5 (commit b030b3b; 91 pass; lint clean): roster check + ack poison; run() survives failing tick; registry done-callback logs crash, stop_loop via asyncio.wait; new MatchRepository.apply_tick(match, events) = events + match update in ONE transaction under write_lock; stale (missing/non-RUNNING match) messages acked, abandon only for another RUNNING match (shortcut: single shared queue); registry.clear(match_id). Re-review (fresh sonnet reviewer after session restart): all 4 ADDRESSED, no new breakage, Approved.
Task 6: complete (commits e4868e3..b030b3b, review clean).
Minors deferred (Task 6): (a) cancel() sends no "ended" broadcast and clears listeners — Task 9/10 cancel/reset routes must notify/close host WS themselves BEFORE calling cancel; (b) no `reset` method — Task 9 maps reset = cancel + create_match; (c) no test for registry crash-logging / stop_loop caller-cancel; (d) persistent apply_tick failure keeps match RUNNING (logs each tick); (e) pulls after ends_at still count in final tick; (f) foreign RUNNING-match messages still abandoned (single shared queue).

Interfaces for downstream (from task-6-report): ConflictError -> 409, MatchNotFoundError -> 404; MatchService(*, matches, players, events, queue, registry, settings, clock) with create_match(duration_s=None), get_match_view(id)->MatchState, update_duration(id,s), start(id) (sync, needs running loop), async cancel(id); MatchRegistry add_listener/remove_listener/broadcast/clear/is_running/start_loop/stop_loop; Broadcast = Callable[[dict], Awaitable[None]]; tick payload {type:"tick", rope, remainingS, delta{inter,gremio}, scores{inter{pulls},gremio{pulls}}}; ended payload {type:"ended", result, endReason, finalRope} (WS layer adds analytics).

NEXT: Task 7 (analytics service). BASE = HEAD after this docs commit.
