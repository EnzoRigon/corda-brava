# Task 8 Report — Player API: public info + join, deps wiring, player token

**Date:** 2026-11-04
**Status:** DONE (commit d4df65a)

## 1. Files

| File | Purpose |
|------|---------|
| `backend/app/api/deps.py` | `Container` dataclass, `build_container`, `get_container(app)`, `container_dep`, `ContainerDep` |
| `backend/app/api/player.py` | Router (prefix `/api/matches`): public + join |
| `backend/app/schemas/player.py` | `JoinRequest/Response`, `PublicMatch` etc. (camelCase fields) |
| `backend/app/services/player_session.py` | Player JWT issue/verify |
| `backend/app/core/app_factory.py` | stores `app.state.settings`, registers router + exception handlers |
| `backend/tests/api/test_player_join.py` | 12 tests |

## 2. Routes

- `GET /api/matches/{id}/public` -> `{status, teams:{inter:{name,colors:{primary,secondary}}, gremio:{...}}, counts:{inter,gremio}, durationS}`. 404 if unknown.
- `POST /api/matches/{id}/players` body `{name, team, deviceId}` -> `{playerId, playerToken, team}`.
  - name trimmed, 1..24 chars; team must be `inter|gremio`; deviceId 1..128 (all 422 on violation).
  - Existing `(match, deviceId)` player: returned as-is (same playerId/team, name/team in body ignored), fresh token, even when match is not LOBBY.
  - New player and match not LOBBY: 409 `{"detail": "A partida já começou"}`.
  - `UniqueConstraintError` race falls back to the existing player.

## 3. Deps

`Container(settings, matches, players, events, queue, registry, service)` is built lazily (bootstrap_db, repos, `make_event_queue`, `MatchRegistry`, `MatchService`) on first request and cached in `app.state.container`. DB path = `DATABASE_URL` minus `sqlite:///`. Routes use `ContainerDep`. Tests: `create_app(Settings(DATABASE_URL=sqlite:///tmp.db, ...))`, then `get_container(app)` to reach `.service/.matches/.players`; alternatively set `app.state.container` or `app.dependency_overrides[container_dep]`. Note: `api/auth.py` `require_host` still uses the `get_settings` lru dependency; Task 9 may prefer `c.settings` (host tests then override `get_settings`, or switch require_host to the container).

## 4. Player token (for Task 9 `/pulls` and `/me`)

```python
issue_player_token(match_id, player_id, device_id, settings) -> str
verify_player_token(token, settings) -> {"match_id","player_id","device_id"} | None   # never raises; requires role=="player"
```
HS256, SECRET_KEY, claims `role="player"`, `match_id`, `player_id`, `device_id`; no expiry. The `Player.token` column stores the token issued at creation; rejoin issues a fresh equivalent token (not persisted). Pulls should verify the token and match `player_id`/`match_id` against the body/path.

## 5. Exception mapping (app-level handlers)

`ConflictError` -> 409 `{"detail": str(exc)}`; `MatchNotFoundError` -> 404 `{"detail": "Partida não encontrada"}`. Services/routes just raise them.

## 6. Results

107 tests pass (95 + 12); ruff and black clean.

## 7. Deviations / notes

- `LATE_JOIN_POLICY=spectator` currently also rejects *new* joins with the same 409 (no spectator player concept in the domain); spectator UX is deferred to the frontend/later task.
- `get_container` takes the `FastAPI` app (not Request); `container_dep` is the Depends-able wrapper.
- Player-facing 404 text "Partida não encontrada" added by me.
- Event-queue `start()` is not called by the container (Task 10 lifespan / start route may need it).
