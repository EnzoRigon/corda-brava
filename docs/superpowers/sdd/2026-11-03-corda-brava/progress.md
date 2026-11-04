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

Task 7: implemented (commit a56f7fb; report 8abc1cc; 95 pass; lint clean). compute_analytics(match, players, events, top_n=5) -> AnalyticsPayload (serialize model_dump(mode="json")); camelCase keys: result, endReason, durationS, totalPlayers, playersPerTeam{inter,gremio}, totalPulls{overall,inter,gremio}, pullsPerSecond[{t,inter,gremio}] (dense), peak{value,t}, finalRope, teams{inter,gremio}{players,totalPulls,avgPullsPerPlayer,bestPlayer,worstPlayer}, players[{playerId,name,team,pulls,pctOfTeam,pctOfAll,pullsPerSec}], leaderboard[].
Task 7: review (sonnet-1M) — Spec ✅, Quality Approved. No Critical/Important.
Task 7: complete (commits 5f3a796..a56f7fb, review clean).
Minors deferred (Task 7): (a) durationS on WIN derived from last pull second+1 (Match has no finished_at; optional: add Match.finished_at set in consumer); (b) CASE MISMATCH — analytics `result` lowercase ("inter") vs WS `ended.result` uppercase ("INTER|GREMIO|DRAW") — Task 10/16 must normalise or document; (c) unpinned edge tests (event after durationS, pre-start clamp, unknown player).

NEXT: Task 8 (player API: public info + join, player token). BASE = HEAD after this docs commit.

Task 8: implemented (commit d4df65a; report de2db86; 107 pass; lint clean). deps.py Container (settings, repos, queue, registry, service) lazily cached on app.state.container, routes use ContainerDep, tests override via app.state.container / dependency_overrides[container_dep]. player_session.py: issue_player_token(match_id, player_id, device_id, settings), verify_player_token(token, settings) -> {match_id, player_id, device_id} | None (role=player, never raises, no exp). Routes: GET /api/matches/{id}/public -> {status, teams{inter,gremio{name,colors{primary,secondary}}}, counts, durationS}; POST /api/matches/{id}/players {name,team,deviceId} -> {playerId,playerToken,team}. App-level handlers ConflictError->409, MatchNotFoundError->404 ("Partida não encontrada").
Task 8: review (sonnet-1M) — Spec ✅, Quality Approved. No Critical/Important.
Task 8: complete (commits 1b09fd6..d4df65a, review clean).
Minors deferred (Task 8): (a) require_host uses global get_settings vs container settings -> FIX IN TASK 9 (depend on container_dep); (b) queue/consumer never started -> Task 10 lifespan/start route owns it; (c) lazy non-locked container init -> build eagerly in create_app/lifespan (Task 9/10); (d) re-join issues fresh token != persisted Player.token — never compare against Player.token; (e) LATE_JOIN_POLICY=spectator collapses to 409 (no spectator domain concept; frontend can show read-only from public status).

NEXT: Task 9. BASE = HEAD after this docs commit.

Task 9: implemented (commit f148cca; report 17a636d; 116 pass; lint clean). POST /api/matches/{id}/pulls {playerId,playerToken,count,clientTs,batchId} -> 202 {accepted}; 401 bad token, 403 token for other player/match or player not in match, 409 "A partida não está em andamento", 422 count<1, count clamped to MAX_PULLS_PER_BATCH. Ingest dedup: Container.seen_batches["matchId:batchId"] -> expiry (BATCH_DEDUP_TTL_S, pruned per request; shortcut: per-process). Queued PullEvent{id,match_id,player_id,team(from stored player),count,client_ts,server_ts,batch_id} — matches consumer.py. GET /api/matches/{id}/me?playerId=&token= -> {screen wait|play|end, team, matchStatus (lowercase), result? (UPPERCASE, only FINISHED)}.
Task 9: review (sonnet-1M) — Spec ✅, Quality Approved. No Critical/Important.
Task 9: complete (commits ac22e53..f148cca, review clean).
Minors deferred (Task 9): (a) batch marked seen BEFORE enqueue — enqueue failure would lose the batch on retry (fix: set after await or pop in except); (b) in-memory queue message id = bare batch_id (cross-match collision, pre-existing; key on match_id+batch_id); (c) 422 count check runs after 409; (d) no test for TTL expiry / per-match dedup scope.

NEXT: Task 10 (host routes + WS) — closes Phase B. Must also pick up deferred minors: Task 5 (a,b: require exp, pin alg test), Task 6 (a: cancel/reset notify/close WS before cancel; b: reset = cancel + create_match), Task 7 (b: analytics result lowercase vs WS ended uppercase), Task 8 (a: require_host via container settings; b: start queue/consumer; c: eager container in create_app/lifespan).

Task 10: implemented (commit fae2c79; report abc73a3; 142 pass; lint clean). Host routes under /api/host (login, create 201 {matchId,joinUrl,qrPayload,config}, GET, PATCH, start, cancel, reset 201 -> new match, analytics 409 until FINISHED), all but login behind require_host. WS /api/host/matches/{id}/ws?token= : bad token/unknown match -> accept+close 1008; snapshot first, then player_joined/tick/ended(+analytics); extra messages {type:"cancelled"} and {type:"reset",newMatchId} then server closes socket. New setting PUBLIC_BASE_URL (joinUrl = <base>/j/<id> = qrPayload). Lifespan builds container eagerly, queue.start(), shutdown registry.stop_all() + queue.close(). Fixed deferred minors 5a/5b, 6a/6b, 7b (result UPPERCASE everywhere), 8a/8b/8c.
Task 10: review (sonnet-1M, pytest x2 stable) — Spec ✅, Quality Approved, minors only.
Task 10: polish round (commit c62590d; report 6ad5b57; 144 pass; lint clean) — controller chose to fix frontend-relevant minors before Phase C: match status UPPERCASE in /me matchStatus and /public status too; PT-BR auth errors ("Token de host inválido ou ausente", "Falha ao entrar na partida"); login rate limit per IP (5 failures / 60 s sliding -> 429 "Muitas tentativas. Tente novamente em instantes"; shortcut: in-memory on Container); HS512 test key 64 bytes; WS test deadline. Verified by controller: 144 pass, ruff + black clean (no separate re-review: changes were reviewer-specified minors).
Task 10: complete (commits 540042b..c62590d, review clean).
Minors deferred (Task 10): (a) natural finish clears listeners, so a host WS left open after `ended` gets no later reset/cancelled message — frontend navigates from the HTTP reset response; (b) ws.py relies on catching RuntimeError after server-side close; (c) one pytest warning remains (untraced).
FRONTEND NOTES (Tasks 11–16): status and result always UPPERCASE; endReason lowercase; WS types snapshot|player_joined|tick|ended|cancelled|reset; async host routes need `with TestClient(app)` in tests; full shapes in task-10-report.md.

## PHASE B COMPLETE (Tasks 6–10). Backend: 144 tests passing.
NEXT: Phase C — Task 11 (frontend scaffold: theme tokens, types, api client, useDeviceId). BASE = HEAD after this docs commit.

## PHASE C — Frontend
Task 11: implemented (commit c1ecbdf; report dfa9579). frontend/: React 18 + Vite + TS strict, react-router-dom 6, vitest+jsdom, ESLint 10 flat config (eslint.config.js — deviation from .eslintrc), separate vitest.config.ts. src/types/api.ts mirrors backend JSON; src/api/client.ts (ApiError{status, detail PT-BR}), hostApi.ts, playerApi.ts; useDeviceId (getDeviceId exported, localStorage try/catch). Env: VITE_API_BASE / VITE_WS_BASE default "" (same-origin), VITE_PUBLIC_BASE default location.origin. Dev proxy /api (+ws) -> :8000. Theme tokens + CSS vars (inter #E5050F, gremio #0D80BF/#4FA9DC), Press Start 2P woff2 from @fontsource copied into src/assets/fonts/ with OFL-LICENSE.txt. Routes: /host/login|create|lobby/:id|match/:id|results/:id, /j/:id, /j/:id/wait|play|end (match /me screen values), / -> /host/login; placeholders live in App.tsx.
Task 11: review (sonnet-1M) — Spec ✅, Quality Approved; all types verified field-by-field against backend.
Task 11: polish round (commit 4ff58fc; report 6c2e433): WS player_joined.team now lowercase (backend api/player.py + test) so team ids are lowercase EVERYWHERE; TeamUpper removed; LoginResponse.expiresAt: string (ISO-8601); client returns undefined on 204/empty body. Verified by controller: backend 144 pass; frontend vitest 3/3, tsc clean.
Task 11: complete (commits 7a88784..4ff58fc, review clean).
Minors deferred (Task 11): (a) getDeviceId returns a new id per call when storage is blocked (hook stable per mount); (b) vitest.config.ts duplicates vite config; (c) placeholders inline in App.tsx (later tasks split pages).
FRONTEND NOTES update: team ids lowercase everywhere ("inter"|"gremio"); status/result UPPERCASE; endReason lowercase.

NEXT: Task 12 (Mascot/Crest components — copy owner-authored asset files only). BASE = HEAD after this docs commit.

Task 12: implemented (commit 7c253ad; report 199713a; frontend vitest 7/7, tsc/build/lint clean). 12 owner files copied verbatim (cmp-verified) to frontend/src/assets/mascots/ (saci_*/mosq_* master.png, pull/happy/defeat/cry.gif) and frontend/src/assets/crests/ (inter.png, gremio.png). <Mascot team state size=128 className /> with state idle->master, straining->pull, winning|happy->happy, losing->defeat, crying->cry; gremio mirrored scaleX(-1) (sprites face right, same as owner prototype); <Crest team size=48 className />. image-rendering: pixelated; PT-BR alt. Draw result -> caller passes idle.
Task 12: review (sonnet-1M) — Spec ✅, Quality Approved. Art policy holds (no drawing code), byte-identical copies re-verified.
Task 12: complete (commits 679137c..7c253ad, review clean).
Minors deferred (Task 12): (a) only 4 of 12 state/team combos tested; (b) fixed square width/height may distort non-square sprites/crests — check in layout (Tasks 14/16), use object-fit: contain if needed.

NEXT: Task 13 (usePullBuffer). BASE = HEAD after this docs commit.

Task 13: implemented (commit 8627ee8; report d881a7f; vitest 13/13). usePullBuffer({matchId, playerId, playerToken, flushIntervalMs, enabled?}) -> {displayCount, tap}. CONTROLLER RULING (idempotency): a failed batch (network/5xx/408/429) is kept in `unacked` and resent with the SAME batchId — never merged into a new batchId (a lost response would double-count); server dedups by batchId. One in-flight request; batches clamped to MAX_PULLS_PER_BATCH=200 (matches backend), excess stays pending. Flush on visibilitychange(hidden)/pagehide via sendBeacon(Blob application/json) with fetch keepalive fallback; beacon never clears `unacked`.
Task 13: review (sonnet-1M) — Spec ✅, Quality Approved; double-count/race/stale-closure traces clean.
Task 13: polish round (commit f08a3bd; report 6bd3cf0; vitest 17/17, tsc/build/lint clean): any 4xx except 408/429 drops the batch (no poison-batch blocking); after 401/403/409 a `stopped` ref zeroes pending and halts flush/flushOnHide until enabled/ids/token change (taps still bump displayCount); stronger tests (beacon Blob body/type, beacon-then-interval same batchId, tap during inflight, 422 drop, stop after 409). Verified by controller: vitest 17/17, tsc clean.
Task 13: complete (commits 64cbc62..f08a3bd, review clean).
Minors deferred (Task 13): (a) no test for stop-flag reset on id/token change or 401/403 stop paths; (b) beacon to a cross-origin API_BASE would need CORS preflight — fine same-origin/proxied (note for Task 17 Docker).

NEXT: Task 14 (player pages). BASE = HEAD after this docs commit.

Task 14: implemented (commit 9cd6e92; report e32a059; vitest 25/25). Pages PlayerJoin (/j/:id: /public teams+crests+counts, name trim/cap 24, team radio, join with deviceId, API detail verbatim e.g. 409 "A partida já começou"), PlayerWait ("Aguardando o host iniciar", mascot idle), PlayerPlay (PullButton PUXAR + CSS "+1", usePullBuffer flush 500ms enabled only on screen=play, mascot straining), PlayerEnd (result + "Obrigado por jogar!", no analytics; mascot happy/crying, idle on DRAW). Session localStorage `cb.session.<matchId>` = {playerId, playerToken, team} (try/catch). useMePolling polls /me 1s, navigates (replace) to /j/:id/<screen>; missing session/401/403 -> clear + back to join. Join -> /wait, wait forwards to real screen (one extra hop).
Task 14: review (sonnet-1M) — Spec ✅, Quality Approved; reload/no-leak/no-loop/no-double-fire/multi-touch all confirmed.
Task 14: polish round (commit 7ecccb8; report f8c3385; vitest 31/31, tsc/build/lint clean): /me in-flight guard (no overlapping polls), polling stops on end, 404 treated like 401/403; PullButton pops keyed by counter ref, button!==0 ignored, context menu blocked; new PullButton + polling tests. Verified by controller: vitest 31/31, tsc clean.
Task 14: complete (commits 69fdbe4..7ecccb8, review clean).
Minors deferred (Task 14): (a) taps in the last ~second before screen flips to end are dropped (server would 409 anyway); (b) no tests for PlayerPlay enabled gating / PlayerEnd mapping; (c) not checked on a real phone/browser (Task 18 E2E).

NEXT: Task 15 (useHostSocket). BASE = HEAD after this docs commit.

Task 15: implemented (commit 5635b13; report c40caee; vitest 41/41). useHostSocket(matchId, token) -> {status, snapshot, lastTick, ended(+analytics), terminal(cancelled|reset{newMatchId}), connected, authError}; reconnect only on unexpected close (500ms x2 backoff, cap 5s, reset on open); never after 1008/ended/cancelled/reset/unmount; snapshot replaces state; player_joined deduped. Host token sessionStorage["cb.hostToken"] (HOST_TOKEN_KEY, getHostToken in HostLogin.tsx). Pages HostLogin, HostCreate (duration 30–600 hardcoded, mirrors backend), HostLobby (qrcode.react QR, fullscreen overlay, TeamColumn/PlayerIcon generic initial block, Start disabled until >=1 player). Art policy holds.
Task 15: review (sonnet-1M) — Spec ✅, Changes requested: 1 Important — lobby reload fell back to window.origin (localhost) for joinUrl -> QR unusable on phones.
Task 15: fix round 1/5 (commit 1a152d4; report d160d7d; backend 144 pass, frontend 42/42, tsc/build/lint clean): MatchView.joinUrl (GET + WS snapshot) via shared _join_url() from PUBLIC_BASE_URL; lobby uses snapshot.joinUrl ?? router state ?? fallback; create_app(settings=None) -> get_settings() so README `uvicorn app.core.app_factory:create_app --factory` works; socket cleanup nulls onmessage/onopen; JSON.parse try/catch; QR overlay aria-modal + focus mgmt; reset follows newMatchId to /host/lobby/<id>. Verified by controller live: README uvicorn command starts; POST create + GET both return joinUrl.
Task 15: complete (commits e893ca6..1a152d4, review clean after fix).
Minors deferred (Task 15): (a) no tests for HostCreate / reconnect snapshot replacement / lobby status navigation; (b) duration bounds hardcoded in HostCreate.
Ruling (dev run): added .claude/launch.json (backend uvicorn :8000 with --host 0.0.0.0, frontend vite :5173) so the user can watch the app in dev mode. For phones on LAN set PUBLIC_BASE_URL=http://<LAN-IP>:5173 (and Vite must listen on 0.0.0.0 — Task 17/18 docs).

NEXT: Task 16 (HostMatch + HostResults). BASE = HEAD after this docs commit.
