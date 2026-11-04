# Task 10 Report — Host API routes + host WebSocket

**Date:** 2026-11-04
**Status:** DONE (closes backend Phase B)
**Commit:** `fae2c79` — `feat(api): host routes + host WebSocket (snapshot/tick/ended) + tests`
**Tests:** 142 pass (116 prior + 26 new/changed); `ruff check .` and `black --check .` clean; `/docs` and `/openapi.json` return 200.

---

## 1. Files

Created: `backend/app/api/host.py`, `backend/app/api/ws.py`, `backend/app/schemas/match.py`, `backend/tests/api/test_host_routes.py`, `backend/tests/api/test_host_ws.py`.
Modified: `api/auth.py`, `api/deps.py` (docstring), `api/player.py`, `core/app_factory.py`, `core/settings.py`, `services/analytics.py`, `services/host_session.py`, `services/match_service.py`, `services/registry.py`, `tests/services/test_analytics.py`, `tests/services/test_host_session.py`.

New setting: `PUBLIC_BASE_URL` (default `http://localhost:5173`); `joinUrl = <PUBLIC_BASE_URL>/j/<matchId>`, `qrPayload` is the same string. Set it to the LAN IP / public host in deploys.

---

## 2. HTTP routes (all under `/api/host`; JSON is camelCase)

All except login need `Authorization: Bearer <token>`, otherwise 401 `{"detail": "Invalid or missing host token"}` with `WWW-Authenticate: Bearer`. Unknown match id gives 404 `{"detail":"Partida não encontrada"}`.

| Route | Request | Success | Errors |
|---|---|---|---|
| `POST /login` | `{password}` | 200 `{token, expiresAt}` | 401 `{"detail":"Senha incorreta"}` |
| `POST /matches` | `{durationS?, balanceMode?: "raw"\|"normalized"}` | 201 `CreateMatchResponse` | 422 `Duração fora do intervalo permitido` (outside `MATCH_DURATION_MIN_S..MAX_S`) |
| `GET /matches/{id}` | - | 200 `MatchView` | 404 |
| `PATCH /matches/{id}` | `{durationS}` | 200 `ConfigOut` | 409 outside LOBBY; 422 out of range; 404 |
| `POST /matches/{id}/start` | - | 200 `MatchView` (status `RUNNING`) | 409 not in LOBBY; 404 |
| `POST /matches/{id}/cancel` | - | 200 `MatchView` (status `FINISHED`, `result` null) | 404 |
| `POST /matches/{id}/reset` | - | **201 `CreateMatchResponse` of the NEW match** | 404 |
| `GET /matches/{id}/analytics` | - | 200 `AnalyticsPayload` (§15) | 409 `A partida ainda não terminou` unless FINISHED; 404 |

`CreateMatchResponse`:
```json
{"matchId":"ABC123","joinUrl":"http://host:5173/j/ABC123","qrPayload":"http://host:5173/j/ABC123",
 "config": <ConfigOut>}
```
`ConfigOut`:
```json
{"durationS":120,"ropeTarget":100,"balanceMode":"normalized",
 "teams":{"inter":{"id":"inter","name":"Inter","colors":{"primary":"#E5050F","secondary":"#FFFFFF"}},
          "gremio":{"id":"gremio","name":"Grêmio","colors":{"primary":"#0D80BF","secondary":"#000000"}}}}
```
`MatchView` (also the `match` body of the WS `snapshot`):
```json
{"id":"ABC123","status":"LOBBY|RUNNING|FINISHED","config":<ConfigOut>,
 "roster":{"inter":[{"id":"..","name":".."}],"gremio":[]},
 "rope":0.0,"remainingS":120.0,
 "scores":{"inter":{"pulls":0},"gremio":{"pulls":0}},
 "result":null,"endReason":null}
```
`result` is `"INTER"|"GREMIO"|"DRAW"|null`, `endReason` is `"win"|"timeout"|null` (lowercase, as the consumer emits it), `status` is uppercase per §14. Note: the public `/me` and `/public` endpoints still return `matchStatus` / `status` in the enum's lowercase form (`"lobby"`); only host payloads use uppercase.

---

## 3. WebSocket `WS /api/host/matches/{id}/ws?token=<hostToken>`

Always `accept()`ed first. Invalid/missing token or unknown match: close with code **1008** straight away. Otherwise a listener is registered in `MatchRegistry` and the snapshot is sent immediately. Client messages are ignored. Listener removed on disconnect.

Server messages (exact shapes):

```json
{"type":"snapshot","match":<MatchView>}
{"type":"player_joined","team":"INTER|GREMIO","player":{"id":"..","name":".."}}
{"type":"tick","rope":-12.5,"remainingS":97.4,"delta":{"inter":8,"gremio":3},
 "scores":{"inter":{"pulls":140},"gremio":{"pulls":95}}}
{"type":"ended","result":"INTER|GREMIO|DRAW","endReason":"win|timeout","finalRope":-100.0,
 "analytics":<AnalyticsPayload>}
{"type":"cancelled"}
{"type":"reset","newMatchId":"XYZ789"}
```
- `tick` is sent every `TICK_INTERVAL_MS` while RUNNING (also on the final tick, right before `ended`). `remainingS` is a float.
- `ended` is the consumer's message plus `analytics`, which the WS listener adds (computed from the DB after the final tick is durable). The socket stays open after `ended`.
- `cancelled` and `reset` are NOT in §14 (the spec defines nothing for cancel). After sending either, the server closes the socket (code 1000). The frontend must handle both: `cancelled` means go back to the create screen; `reset` means navigate to `newMatchId`'s lobby.
- `player_joined` is emitted only when a NEW player joins (not on an idempotent re-join). Joins after LOBBY are rejected with 409 so none arrive mid-match.

---

## 4. Reset / cancel semantics

- **cancel:** broadcast `{"type":"cancelled"}` to listeners, then `service.cancel` (stops the consumer, status FINISHED, no result, listeners cleared). Returns the `MatchView`. Works in any status (idempotent on FINISHED).
- **reset:** creates the new LOBBY match first (same `durationS` and `balanceMode` as the old one; players do not carry over), broadcasts `{"type":"reset","newMatchId"}` on the OLD match's listeners, then cancels the old one. Order differs from the brief (notify, cancel, create) only so the message can carry `newMatchId`. Returns 201 with the new match's `CreateMatchResponse`.

## 5. Lifecycle wiring

- `create_app` now has a `lifespan`: it builds the Container eagerly (`get_container`: DB bootstrap, queue, registry, service), awaits `queue.start()`, and on shutdown calls the new `MatchRegistry.stop_all()` and `queue.close()`. `get_container` keeps its lazy fallback so tests that do not enter the lifespan (plain `TestClient(app)`) still work; `test_health` does not create a DB file.
- The consumer's broadcast callback was already `registry.broadcast(match_id, ...)` (set in `MatchService.start`); the WS registers its listener on the same registry, so ticks reach it. No additional wiring was needed.
- `start`, `cancel`, `reset` are `async def` routes (the consumer task needs the running loop). Tests must use `with TestClient(app) as client:` so one portal/loop persists across requests.
- `join` in `player.py` became `async def` to await the `player_joined` broadcast.
- `require_host` now takes `ContainerDep` and uses `c.settings` (no global `get_settings`).

## 6. Result casing decision

Uppercase everywhere: WS `ended.result`, `/me` `result`, host `MatchView.result`, and `AnalyticsPayload.result` (changed from lowercase; `test_analytics` updated). `endReason` stays lowercase (`win|timeout`) in all payloads, as §14 shows. `team` inside analytics player stats stays lowercase (`"inter"`), while `player_joined.team` is uppercase as in §14.

## 7. Deferred minors fixed

- Task 5a: `jwt.decode(..., options={"require": ["exp"]})` plus test for a token with no `exp`.
- Task 5b: tests that `alg=none` and HS512 tokens are rejected (the HS512 test emits one PyJWT short-key warning in the suite).
- Task 6a/6b: cancel/reset notify listeners before `service.cancel`; reset = notify + cancel + new match, returned.
- Task 7b: casing unified (above). Task 8a: `require_host` uses container settings (its test now overrides `container_dep`).
- Task 8b/8c: lifespan starts/closes queue, eager container build, loops stopped on shutdown.
- `registry.broadcast` already iterated a copy and dropped dead listeners; made one tiny fix: `.get(match_id, set()).discard(cb)` so a concurrent `clear` cannot raise `KeyError`.

Not touched (still deferred): Task 6 c-f, Task 7 a/c, Task 8 d/e, all of Task 9 a-d, Task 5c.

## 8. Tests (26 new/changed)

`test_host_routes.py` (login ok/401; 7 unauthenticated 401s; create + joinUrl; create 422; GET view and 404; PATCH ok/422; start then PATCH/start 409; cancel; reset; analytics 409 then 200), `test_host_ws.py` (no token and bad token close 1008; snapshot first with roster/rope/remaining/scores; `player_joined` once with idempotent re-join; tick then ended with analytics and matching result casing; reset and cancel notifications), plus 2 session tests (no-exp, alg). Every WS receive is bounded (1 s match, messages guaranteed).

## 9. Deviations

- Tests were written together with the implementation in one pass rather than watched failing first (all passed on first run).
- Extra WS message types `cancelled` and `reset` (not in §14); reset order as noted above.
- Analytics endpoint returns 409 for a non-FINISHED match (not specified).
- No login rate limiting (spec says "lightly"; left for a later task).
