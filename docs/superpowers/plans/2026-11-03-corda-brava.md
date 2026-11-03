# Corda Brava Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete "Corda Brava" tug-of-war party game — FastAPI backend (domain rules, SQLite repos, swappable queue, single-writer consumer loop, host auth, WS) + React/Vite frontend (host big-screen + player phone flows, pixel-art mascots, analytics) + Docker Compose stack on one port.

**Architecture:** Clean layering. Pure domain game-rules (no IO) → repository-abstracted SQLite → broker-shaped `EventQueue` (in-memory now) → per-match single-writer asyncio consumer loop that is the sole writer of runtime state → FastAPI routers + host WebSocket. Frontend talks to one origin through a proxy; host drives a WS, players POST batched pulls. Owner-authored mascot sprites and crests are **copied** into the frontend as static assets (never re-rendered in code).

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, pydantic-settings, stdlib sqlite3, PyJWT, pytest+httpx; React 18, Vite, TypeScript (strict), react-router, Recharts, qrcode.react, Press Start 2P (bundled OFL); Docker + nginx proxy.

**Spec:** `prompt.md` (authoritative) + `docs/superpowers/specs/2026-11-03-corda-brava-design.md` (decisions). Executors read both.

## Global Constraints

- Python **3.11+**; FastAPI; Pydantic **v2** + pydantic-settings for all schemas/settings.
- SQLite **only behind repository interfaces** (ABC/Protocol); no sqlite types leak past repos; WAL mode; serialized writes.
- `EventQueue` is **broker-shaped**: async, `receive_batch(max, wait)` leases (not drains), explicit `ack()` after durable apply, idempotent redelivery by `batchId`. No in-memory-only semantics.
- Consumer loop is the **single writer** of match runtime state; ingest endpoint only enqueues.
- Server-authoritative timer (`started_at`/`ends_at`, remaining computed from clock).
- Host token: constant-time password compare (`secrets.compare_digest`), signed (PyJWT) `role=host`+expiry via `SECRET_KEY`; `require_host` dep for HTTP; WS token via `?token=` query param, invalid → close 1008.
- One player per device: `(match_id, device_id)` unique; rejoin idempotent.
- Frontend **strict TS**; React function components + hooks; no Redux.
- **All player-facing copy PT-BR**; code/identifiers/comments English.
- Pixel font self-hosted (bundled OFL file, no hotlink); `image-rendering: pixelated`.
- **No copyrighted/web-downloaded art.** Mascot sprites (`docs/mascot-references/mascot-test/assets/*`) and crests (`docs/logo-references/*.png`) are owner-authored committed files — copy them as-is; do not generate renditions of the clubs' mascots/crests in code.
- Game name "Corda Brava" consistently. Rope convention: `-ROPE_TARGET`=Inter(left), `+ROPE_TARGET`=Grêmio(right), 0=center.
- All tunables from env/settings with defaults per `prompt.md §4`; ship `.env.example`.
- Whole stack runs via `docker compose up` on a single public port; dev override gives hot reload; SQLite persists via named volume.

## Review Focus

- **Pull batch retried after a network timeout** (same `batchId` redelivered by the queue, or client resend): must be counted **exactly once**. Owned by Task 4 (queue dedup/redelivery) + Task 6 (consumer idempotency) + Task 10 (ingest dedup ack).
- **Match timer expiry with the rope off-center but not at threshold:** must resolve **DRAW** (`end_reason=timeout`), not award the closer side. Owned by Task 2 (`resolve_result`).
- **Normalized scoring with a 0-player team:** divide-by-zero avoided via `max(count,1)`; empty team contributes 0, never NaN/crash. Owned by Task 2.
- **Host WS reconnect mid-match:** on connect the client receives a **full snapshot** (not just deltas) so the scene resyncs; consumer loop keeps running across the disconnect. Owned by Task 7 (WS snapshot-on-connect) + Task 6 (loop independent of WS).
- **Player reload mid-match:** `GET /me` restores the correct screen (`wait|play|end`) from device token; no duplicate player row. Owned by Task 9 (`/me`) + Task 8 (idempotent join) + Task 15 (`useDeviceId` restore).

---

## PHASE A — Backend core (domain → repos → queue → auth)

### Task 1: Backend skeleton — settings, app factory, domain entities & enums

**Files:**
- Create: `backend/app/core/settings.py`, `backend/app/core/app_factory.py`, `backend/app/core/logging.py`
- Create: `backend/app/domain/enums.py`, `backend/app/domain/entities.py`
- Create: `backend/pyproject.toml`, `backend/app/__init__.py` (+ package `__init__.py`s)
- Create: `backend/app/api/health.py` (GET `/health` → `{"status":"ok"}`)
- Test: `backend/tests/test_settings.py`, `backend/tests/test_health.py`

**Interfaces:**
- Produces: `Settings` (pydantic-settings BaseSettings) with every var in `prompt.md §4` typed with defaults; `get_settings()` cached accessor. `create_app(settings) -> FastAPI` app factory mounting `/health` and `/api` router root. Enums `MatchStatus{LOBBY,RUNNING,FINISHED}`, `Team{INTER,GREMIO}`, `MatchResult{INTER,GREMIO,DRAW}`, `EndReason{WIN,TIMEOUT}`, `BalanceMode{RAW,NORMALIZED}`, `QueueBackend{MEMORY,AZURE_SERVICE_BUS}`. Dataclass/Pydantic domain models `Match`, `Player`, `PullEvent`, `TickInput`, `MatchState` with fields per `prompt.md §11`.

- [ ] **Step 1:** Write `test_settings.py`: asserts defaults (`HOST_PASSWORD=="Inter>Gremio"`, `DEFAULT_MATCH_DURATION_S==120`, `ROPE_TARGET==100`, `TEAM_BALANCE_MODE=="normalized"`, `QUEUE_BACKEND=="memory"`) and that env override changes a value. Write `test_health.py`: `TestClient(create_app(...)).get("/health").json()=={"status":"ok"}`.
- [ ] **Step 2:** Run `pytest backend/tests/test_settings.py backend/tests/test_health.py -v` → FAIL (import errors).
- [ ] **Step 3:** Implement enums, domain entities, `Settings`, `get_settings`, `create_app`, `/health`. Configure `pyproject.toml` (deps: fastapi, uvicorn[standard], pydantic, pydantic-settings, pyjwt, httpx, pytest, pytest-asyncio, ruff, black).
- [ ] **Step 4:** Run the two tests → PASS.
- [ ] **Step 5:** Commit `feat(backend): skeleton — settings, app factory, domain entities, health`.

### Task 2: Pure game rules (domain, fully unit-tested)

**Files:**
- Create: `backend/app/domain/rules.py`
- Test: `backend/tests/domain/test_rules.py`

**Interfaces:**
- Consumes: `MatchState`, `TickInput`, enums from Task 1.
- Produces (pure, no IO): `apply_pulls(state: MatchState, tick: TickInput, *, balance_mode, pull_unit, rope_target) -> MatchState` (returns new state with updated `rope_position`); `check_win(rope: float, rope_target: int) -> MatchResult | None`; `resolve_result(state, *, timed_out: bool) -> tuple[MatchResult, EndReason]`; helper `clamp(x, lo, hi)`.

- [ ] **Step 1:** Write tests covering: raw mode net delta `(pulls_gremio - pulls_inter)*PULL_UNIT`; normalized mode `effort=(pulls/max(count,1))*unit` then `delta=effort_gremio-effort_inter`; **0-player team → no NaN, contributes 0**; clamp at `±ROPE_TARGET`; `check_win` returns GREMIO at `>=+target`, INTER at `<=-target`, `None` between; `resolve_result` with `timed_out=True` and rope≠0 → `(DRAW, TIMEOUT)`; with rope at +target → `(GREMIO, WIN)`.
- [ ] **Step 2:** Run `pytest backend/tests/domain/test_rules.py -v` → FAIL.
- [ ] **Step 3:** Implement `rules.py` per `prompt.md §6` formulas exactly.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(domain): pure game rules (apply_pulls/check_win/resolve_result) + tests`.

### Task 3: Repository interfaces + SQLite implementations (WAL, bootstrap)

**Files:**
- Create: `backend/app/repositories/interfaces.py`, `backend/app/repositories/sqlite/connection.py`, `.../match_repo.py`, `.../player_repo.py`, `.../event_repo.py`, `.../bootstrap.py`
- Test: `backend/tests/repositories/test_sqlite_repos.py`

**Interfaces:**
- Produces: Protocols `MatchRepository`, `PlayerRepository`, `EventRepository` with methods returning **domain models only**: `create_match`, `get_match`, `update_match`, `list_players(match_id)`, `add_player`, `get_player_by_device(match_id, device_id)`, `get_player(id)`, `add_event`, `event_exists(match_id, batch_id)`, `list_events(match_id)`. SQLite impls open with WAL + `check_same_thread=False` behind a single write lock. `bootstrap_db(path)` creates tables + indexes + unique constraints per `prompt.md §11`.

- [ ] **Step 1:** Write tests: create/get match round-trips as domain model; `add_player` then second `add_player` same `(match_id, device_id)` raises/returns existing (unique enforced); `event_exists` true after `add_event`, and `add_event` twice same `(match_id,batch_id)` doesn't duplicate (unique); `list_events` ordered by `server_ts`. Use a tmp_path db.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement bootstrap + repos; map rows↔domain models; WAL pragma; write lock.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(repos): repository interfaces + SQLite impls (WAL, unique constraints) + tests`.

### Task 4: EventQueue abstraction + in-memory broker-shaped impl (lease/ack/redelivery)

**Files:**
- Create: `backend/app/queue/interfaces.py` (`QueueMessage`, `EventQueue` Protocol), `backend/app/queue/memory.py`, `backend/app/queue/factory.py`
- Test: `backend/tests/queue/test_memory_queue.py`

**Interfaces:**
- Produces: `QueueMessage{id:str, payload:PullEvent, delivery_count:int}`; `EventQueue` Protocol `start/close/enqueue/receive_batch(max_messages,max_wait_s)/ack(msgs)/abandon(msgs)` exactly per `prompt.md §7`. `InMemoryEventQueue` honoring async + lease (received not deleted; unacked become visible again after `QUEUE_LEASE_TIMEOUT_S`). `make_event_queue(settings) -> EventQueue` returns memory impl for `QUEUE_BACKEND=memory`.

- [ ] **Step 1:** Write tests: `enqueue` then `receive_batch` returns leased msg; `ack` removes it (not redelivered); **kill-before-ack → after lease timeout the same batch is redelivered** (assert redelivery, use a tiny lease timeout); `receive_batch` may return empty within `max_wait_s`; factory returns `InMemoryEventQueue`.
- [ ] **Step 2:** Run (pytest-asyncio) → FAIL.
- [ ] **Step 3:** Implement memory queue + factory.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(queue): broker-shaped EventQueue + in-memory lease/ack/redelivery + tests`.

### Task 5: Host session & auth (login, token, require_host)

**Files:**
- Create: `backend/app/services/host_session.py`, `backend/app/api/auth.py` (deps), `backend/app/schemas/host.py`
- Test: `backend/tests/services/test_host_session.py`

**Interfaces:**
- Produces: `issue_host_token(settings) -> (token, expires_at)` (PyJWT, `role=host`, exp from `HOST_TOKEN_TTL_SECONDS`, signed `SECRET_KEY`); `verify_host_token(token, settings) -> bool`; `check_password(candidate, settings) -> bool` via `secrets.compare_digest`; FastAPI deps `require_host` (Bearer → 401) and `verify_ws_token(token)`.

- [ ] **Step 1:** Write tests: right password → valid token that verifies; wrong password → false; tampered/expired token → verify false; `require_host` dependency rejects missing/bad Bearer.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(auth): host login, JWT token, require_host + tests`.

---

## PHASE B — Backend services, consumer loop, API & WS

### Task 6: Match service (state machine) + pull-consumer loop + match registry

**Files:**
- Create: `backend/app/services/match_service.py`, `backend/app/services/consumer.py`, `backend/app/services/registry.py`
- Test: `backend/tests/services/test_match_service.py`, `backend/tests/services/test_consumer.py`

**Interfaces:**
- Consumes: repos (Task 3), queue (Task 4), rules (Task 2).
- Produces: `MatchService` with `create_match`, `get_match_view`, `update_duration` (LOBBY only, else 409), `start` (LOBBY→RUNNING, spins consumer task), `reset`/`cancel` (tears down). State guards raise a `ConflictError` mapped to 409. `ConsumerLoop.run()`: each `TICK_INTERVAL_MS` → `receive_batch` → **dedup by batch_id via `event_exists`** → aggregate per team → `add_event` (persist) → `apply_pulls` → `check_win`/timer → update runtime (single writer) → **`ack` only after durable apply** → broadcast via injected callback → stop + set FINISHED on win/timeout. `MatchRegistry` keyed by match id (running loops + per-match broadcast callback set).

- [ ] **Step 1:** Write service tests: illegal transition (start twice, patch duration while RUNNING) → ConflictError; start sets `started_at`/`ends_at`. Consumer tests (asyncio, fake queue + in-memory repos + fake clock): enqueue a batch → one tick persists event, moves rope, acks; **redelivered duplicate batch_id applied twice has no extra effect** (idempotent); rope crossing +target → FINISHED/GREMIO/WIN and loop stops; clock past `ends_at` with rope≠0 → FINISHED/DRAW/TIMEOUT.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement service, consumer, registry. Inject broadcast callback (so loop doesn't depend on WS).
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(services): match state machine + single-writer consumer loop + registry + tests`.

### Task 7: Analytics service

**Files:**
- Create: `backend/app/services/analytics.py`, `backend/app/schemas/analytics.py`
- Test: `backend/tests/services/test_analytics.py`

**Interfaces:**
- Consumes: `PullEvent` list, players, match.
- Produces: `compute_analytics(match, players, events) -> AnalyticsPayload` with everything in `prompt.md §15`: result/endReason/durationS, totalPlayers, playersPerTeam, totalPulls overall+per team, `pullsPerSecond` timeline `[{t,inter,gremio}]` (1s buckets), `peak{value,t}`, finalRope; per-team best/worst player, per-player `{pulls, pctOfTeam, pctOfAll, pullsPerSec}`, `avgPullsPerPlayer`, leaderboard top N. Pure-ish functions.

- [ ] **Step 1:** Write tests pinning: 1s bucketing from `server_ts`; best/worst by total pulls per team; percentage math (`pct_of_team`, `pct_of_all`); peak second; empty events → zeros not crash.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(analytics): analytics service + bucketing/best-worst/% tests`.

### Task 8: Player API — public info + join (one-per-device, idempotent)

**Files:**
- Create: `backend/app/api/player.py`, `backend/app/schemas/player.py`; wire `make_event_queue`, repos, services via `Depends` in `backend/app/api/deps.py`
- Test: `backend/tests/api/test_player_join.py`

**Interfaces:**
- Consumes: MatchService, repos, auth (player token issuance — opaque or signed with device+match+player).
- Produces: `GET /api/matches/{id}/public`; `POST /api/matches/{id}/players {name,team,deviceId}` → `{playerId,playerToken,team}`; player-token issue/verify helper. Join validates team against match teams, trims/caps name, **LATE_JOIN block → 409 PT-BR** when not LOBBY. Second join same device → existing player (idempotent, no dup).

- [ ] **Step 1:** Write tests (TestClient): create match (via service directly or host route), join returns player+token; **re-join same deviceId returns same playerId** (no new row); join with invalid team → 422/400; join when RUNNING + block policy → 409 with PT-BR detail "A partida já começou"; public endpoint shows counts.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement deps wiring + player router.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): player public + join (one-per-device idempotent) + tests`.

### Task 9: Player API — pulls ingest (enqueue/dedup/clamp) + `/me`

**Files:**
- Modify: `backend/app/api/player.py`
- Create: `backend/app/schemas/pulls.py`
- Test: `backend/tests/api/test_pulls_and_me.py`

**Interfaces:**
- Consumes: queue, repos, player-token verify.
- Produces: `POST /api/matches/{id}/pulls {playerId,playerToken,count,clientTs,batchId}` → **202** (validates player∈match, match RUNNING, dedup by batchId within `BATCH_DEDUP_TTL_S` → ack without re-enqueue, clamp to `MAX_PULLS_PER_BATCH`, else enqueue PullEvent). `GET /api/matches/{id}/me?playerId=&token=` → `{screen:'wait'|'play'|'end', team, matchStatus, result?}`.

- [ ] **Step 1:** Write tests: pull in RUNNING → 202 and queue has 1 msg; **same batchId again → 202 but queue not re-enqueued** (idempotent ingest); count clamped to MAX; pull when not RUNNING → 409; bad token → 401/403; `/me` returns `wait` in LOBBY, `play` in RUNNING, `end` + result in FINISHED.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): pull ingest (enqueue/dedup/clamp, 202) + /me + tests`.

### Task 10: Host API routes + host WebSocket (snapshot + tick broadcast)

**Files:**
- Create: `backend/app/api/host.py`, `backend/app/api/ws.py`, `backend/app/schemas/match.py`
- Test: `backend/tests/api/test_host_routes.py`, `backend/tests/api/test_host_ws.py`

**Interfaces:**
- Consumes: MatchService, analytics, auth (`require_host`, `verify_ws_token`), registry.
- Produces: `POST /api/host/login`; `POST /api/host/matches`→`{matchId,joinUrl,qrPayload,config}`; `GET /api/host/matches/{id}`; `PATCH /api/host/matches/{id}`; `POST .../start|reset|cancel`; `GET .../analytics`. `WS /api/host/matches/{id}/ws?token=` → validate (bad→accept+close 1008), register in match set, **send full `snapshot` immediately**, then push `player_joined`/`tick`/`ended` messages per `prompt.md §14`. Broadcast iterates a snapshot of the set, drops dead sockets. Consumer's broadcast callback (Task 6) wired to this set.

- [ ] **Step 1:** Write tests: unauth host route → 401; login→token→create match 201; start transitions RUNNING; patch duration in RUNNING → 409; WS without token → closed 1008; WS with token → first message is `type:"snapshot"` with match/roster/rope/remaining; joining a player then reading WS yields `player_joined`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement routes + WS; wire broadcast callback into registry on start; tear down on reset/cancel.
- [ ] **Step 4:** Run → PASS; manually confirm `/docs` renders.
- [ ] **Step 5:** Commit `feat(api): host routes + host WebSocket (snapshot/tick/ended) + tests`.

---

## PHASE C — Frontend

### Task 11: Frontend skeleton — Vite+TS, routing, theme tokens, typed API client, shared types

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json` (strict), `frontend/vite.config.ts`, `frontend/index.html`, `frontend/.eslintrc`, `frontend/src/main.tsx`, `frontend/src/App.tsx` (router), `frontend/src/theme/tokens.ts`, `frontend/src/theme/global.css`, `frontend/src/types/api.ts` (mirror Pydantic), `frontend/src/api/client.ts`, `frontend/src/api/hostApi.ts`, `frontend/src/api/playerApi.ts`, `frontend/src/hooks/useDeviceId.ts`
- Bundle: Press Start 2P font file under `frontend/src/assets/fonts/` + `@font-face`.
- Test: `frontend/src/hooks/useDeviceId.test.ts` (vitest)

**Interfaces:**
- Produces: theme tokens (Inter/Grêmio colors per design, spacing, z-index, pixel font); TS types mirroring §13/§14 messages (`Snapshot`, `TickMsg`, `EndedMsg`, `AnalyticsPayload`, etc.); typed `fetch` client reading `VITE_API_BASE`/`VITE_WS_BASE`/`VITE_PUBLIC_BASE`; `useDeviceId()` (localStorage UUID). Routes: `/host/login|create|lobby/:id|match/:id|results/:id`, `/j/:id` (player join), player wait/play/end.

- [ ] **Step 1:** Write `useDeviceId.test.ts`: returns a stable UUID persisted in localStorage across calls.
- [ ] **Step 2:** Run `npm test` → FAIL.
- [ ] **Step 3:** Scaffold app, routing, theme, types, client, font, `useDeviceId`.
- [ ] **Step 4:** Run → PASS; `npm run build` + `tsc --noEmit` clean.
- [ ] **Step 5:** Commit `feat(frontend): skeleton — vite/ts, routing, theme, typed client, useDeviceId`.

### Task 12: Assets — copy owner sprites + crests + Mascot/Crest components

**Files:**
- Copy (verbatim, via shell): `docs/mascot-references/mascot-test/assets/{saci,mosq}_*.{gif,png}` → `frontend/src/assets/mascots/`; `docs/logo-references/{inter,gremio}.png` → `frontend/src/assets/crests/`
- Create: `frontend/src/components/Mascot.tsx`, `frontend/src/components/Crest.tsx`
- Test: `frontend/src/components/Mascot.test.tsx`

**Interfaces:**
- Produces: `<Mascot team state />` where `state ∈ idle|straining|winning|losing|happy|crying` maps to the owner sprites (idle→`*_master.png`, straining→`*_pull.gif`, winning/happy→`*_happy.gif`, losing→`*_defeat.gif`, crying→`*_cry.gif`); `image-rendering:pixelated`; Grêmio mirrored to face center. `<Crest team />` renders the copied crest png. **No drawing of characters in code — assets are imported files.**

- [ ] **Step 1:** Write `Mascot.test.tsx`: for `team=INTER state=straining` the rendered `<img>` src includes `saci_pull`; `team=GREMIO state=happy` includes `mosq_happy`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Copy assets with `cp`; implement components importing them.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(frontend): copy owner mascot/crest assets + Mascot/Crest components`.

### Task 13: `usePullBuffer` hook (count/flush/retry/batchId/flush-on-hide)

**Files:**
- Create: `frontend/src/hooks/usePullBuffer.ts`
- Test: `frontend/src/hooks/usePullBuffer.test.ts`

**Interfaces:**
- Consumes: playerApi pull POST.
- Produces: `usePullBuffer({matchId,playerId,playerToken,flushIntervalMs}) -> {displayCount, tap()}`. `tap()`: `displayCount++`, `pendingBatch++`, never awaits. Flushes every interval + on `visibilitychange`/`pagehide` (sendBeacon when possible) with fresh `batchId` UUID per batch; snapshot count, clear only on 2xx, **merge back on failure** (no lost pulls). Clamp to `MAX_PULLS_PER_BATCH`.

- [ ] **Step 1:** Write tests (vitest + fake timers, mocked fetch): N taps → displayCount N instantly; after interval one POST with count=N and a batchId; POST rejects → next flush includes the merged-back count (nothing lost); 2xx clears pending.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(frontend): usePullBuffer (batch/retry/merge-back/flush-on-hide) + tests`.

### Task 14: Player flow pages — Join → Wait → Play → End

**Files:**
- Create: `frontend/src/pages/PlayerJoin.tsx`, `PlayerWait.tsx`, `PlayerPlay.tsx`, `PlayerEnd.tsx`, `frontend/src/components/PullButton.tsx`, `frontend/src/hooks/useMePolling.ts`
- Test: `frontend/src/pages/PlayerJoin.test.tsx`

**Interfaces:**
- Consumes: playerApi, useDeviceId, usePullBuffer, `/me` polling.
- Produces: Join (name + team pick, PT-BR, calls join, stores playerToken) → Wait ("Aguardando o host iniciar") → Play (big thumb-reachable PUXAR + "+1" juice, displayCount) → End (result + "Obrigado por jogar!", **no analytics**). `useMePolling` switches screen on `/me` status; mid-match reload restores correct screen from stored token.

- [ ] **Step 1:** Write `PlayerJoin.test.tsx`: renders team options + name input in PT-BR; submitting calls join API with deviceId and navigates to wait.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement pages + PullButton + polling.
- [ ] **Step 4:** Run → PASS; `tsc` clean.
- [ ] **Step 5:** Commit `feat(frontend): player flow (join/wait/play/end) + PullButton + /me polling`.

### Task 15: `useHostSocket` + Host Login/Create/Lobby pages (QR + animated roster)

**Files:**
- Create: `frontend/src/hooks/useHostSocket.ts`, `frontend/src/pages/HostLogin.tsx`, `HostCreate.tsx`, `HostLobby.tsx`, `frontend/src/components/QRCode.tsx`, `TeamColumn.tsx`, `PlayerIcon.tsx`
- Test: `frontend/src/hooks/useHostSocket.test.ts`

**Interfaces:**
- Consumes: hostApi, WS.
- Produces: `useHostSocket(matchId, token) -> {status, snapshot, lastTick, ended, connected}` — connects `?token=`, stores snapshot, applies `player_joined`/`tick`/`ended`, reconnects with backoff, typed messages. HostLogin (password → token in storage), HostCreate (duration/balance → create → navigate lobby), HostLobby (big clickable `QRCode` → fullscreen overlay of `joinUrl` from `VITE_PUBLIC_BASE`, animated roster via TeamColumn/PlayerIcon from snapshot/`player_joined`, Start button).

- [ ] **Step 1:** Write `useHostSocket.test.ts` (mock WebSocket): on open consumes a `snapshot` message and exposes it; a `player_joined` appends to roster; reconnect scheduled on close.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement hook + pages + components.
- [ ] **Step 4:** Run → PASS; `tsc` clean.
- [ ] **Step 5:** Commit `feat(frontend): useHostSocket + host login/create/lobby (QR + animated roster)`.

### Task 16: Host Match scene (rope + mascots + timer, interpolation) + Results + analytics charts

**Files:**
- Create: `frontend/src/pages/HostMatch.tsx`, `HostResults.tsx`, `frontend/src/components/RopeScene.tsx`, `Rope.tsx`, `Timer.tsx`, `ResultBanner.tsx`, `AnalyticsGrid.tsx`, `frontend/src/components/charts/PullsTimeline.tsx`, `frontend/src/hooks/useCountdown.ts`
- Test: `frontend/src/components/RopeScene.test.tsx`

**Interfaces:**
- Consumes: useHostSocket, Mascot/Crest, Recharts, analytics types.
- Produces: HostMatch — `RopeScene` with both mascots (`straining`, intensity scaling with `delta`), knot position from `rope` (`left% = 50 + rope/target*40`, rAF interpolation toward latest tick), `Timer` (`useCountdown` visual interpolation of `remainingS`), juice (shake on big swing, +particles optional). HostResults — winner mascot `happy`, loser `crying` (draw: both exhausted), `ResultBanner` PT-BR, `AnalyticsGrid` tiles + `PullsTimeline` Recharts line/area from `analytics`, "Nova Partida" → reset→create.

- [ ] **Step 1:** Write `RopeScene.test.tsx`: given `rope=-100 target=100` the knot style left ≈ `10%`; `rope=+100` ≈ `90%`; `rope=0` ≈ `50%`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement scene, interpolation, results, charts.
- [ ] **Step 4:** Run → PASS; `tsc` + `npm run build` clean.
- [ ] **Step 5:** Commit `feat(frontend): host match rope scene + results + analytics charts`.

---

## PHASE D — Packaging, docs, end-to-end

### Task 17: Dockerfiles + compose (prod single-port proxy + volume) + dev override + .env.example

**Files:**
- Create: `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` (SPA fallback + `/api` & WS proxy) OR `proxy/` service config, `docker-compose.yml`, `docker-compose.dev.yml`, `.env.example`, `.dockerignore`s
- Test: scripted smoke (in Task 18 loop): `docker compose up -d` then `curl /health`, `curl /` 200.

**Interfaces:**
- Produces: multi-stage backend image (python:3.11-slim, non-root, Uvicorn **single worker**, HEALTHCHECK `/health`); multi-stage frontend (npm ci && build → nginx serving static + SPA fallback + proxying `/api` and WS upgrade headers to backend); base compose = production-shaped (single public port 80, named volume for SQLite, `restart: unless-stopped`, `depends_on` healthcheck); dev override = bind mounts, Uvicorn `--reload`, Vite dev, exposed ports; `.env.example` documents **every** var from `prompt.md §4` incl. `VITE_PUBLIC_BASE`, `SECRET_KEY`, `HOST_PASSWORD` (overridable, no insecure baked value).

- [ ] **Step 1:** Write Dockerfiles, nginx conf (correct `Upgrade`/`Connection` for WS), both compose files, `.env.example`.
- [ ] **Step 2:** `docker compose config` validates both files.
- [ ] **Step 3:** `docker compose up -d --build`; `curl -f localhost/health` and `curl -f localhost/` → 200; data volume present.
- [ ] **Step 4:** `docker compose down`.
- [ ] **Step 5:** Commit `chore(docker): Dockerfiles + prod/dev compose (single port, proxy, volume) + .env.example`.

### Task 18: READMEs + end-to-end Playwright flow + full validation loop

**Files:**
- Create: `README.md` (root), `backend/README.md`, `frontend/README.md`, `frontend/e2e/flow.spec.ts` (Playwright), `frontend/playwright.config.ts`
- Test: the Playwright E2E itself is the test.

**Interfaces:**
- Consumes: the whole running stack.
- Produces: root README (setup local/dev/VPS, LAN/QR note with `VITE_PUBLIC_BASE`, host/player flow, recorded design choices, **"Swapping to Azure Service Bus"** section naming the single file `AzureServiceBusEventQueue` + env vars + "no consumer/service/domain changes", scaling limitation). Playwright E2E: host login → create → read joinUrl → open second context as player → join team → host start → player taps PUXAR repeatedly → host WS rope moves → match ends → player end screen + host analytics visible.

- [ ] **Step 1:** Write the Playwright spec driving two browser contexts (host + player) against the compose stack (or vite+uvicorn dev).
- [ ] **Step 2:** Run E2E → iterate until green.
- [ ] **Step 3:** Write the three READMEs incl. the Azure swap section and VPS/TLS/`wss://` guidance.
- [ ] **Step 4:** Full validation loop (see below) all green.
- [ ] **Step 5:** Commit `feat: READMEs + Playwright end-to-end flow; docs for Azure swap, VPS/TLS`.

---

## Full validation loop (run after each phase and at the end)

1. `cd backend && ruff check . && black --check . && pytest -q` → all pass.
2. `cd frontend && npm run lint && tsc --noEmit && npm test && npm run build` → all pass.
3. `docker compose config` valid; `docker compose up -d --build`; `/health` + `/` 200; `docker compose down`.
4. Playwright E2E green against the running stack.

If any step fails, fix within the owning task and re-run that step.
