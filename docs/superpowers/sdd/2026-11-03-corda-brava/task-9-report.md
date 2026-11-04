# Task 9 Report — Pull ingest + /me

**Date:** 2026-11-04
**Status:** DONE. Commit `f148cca`. 116 backend tests pass (107 + 9 new); ruff and black clean.

## Files
- `backend/app/api/player.py` (added `POST /{id}/pulls`, `GET /{id}/me`)
- `backend/app/schemas/pulls.py` (new: `PullRequest`, `PullAccepted`, `MeResponse`)
- `backend/app/api/deps.py` (`Container.seen_batches: dict[str, float]`)
- `backend/tests/api/test_pulls_and_me.py` (new)

## Routes
### POST `/api/matches/{id}/pulls` -> 202
Request `{playerId, playerToken, count, clientTs, batchId}`. Response `{accepted: <clamped count>}`.
- 401 `Token inválido`: token fails verification.
- 403: valid token whose match_id/player_id claims differ from path/body, or the player is not in the match. Convention: 401 = bad token, 403 = valid token for someone else.
- 404: unknown match (existing handler).
- 409 `A partida não está em andamento`: match not RUNNING (LOBBY or FINISHED).
- 422: `count < 1` (also pydantic errors for missing or invalid fields). Checked after auth and the RUNNING check.
- `count > MAX_PULLS_PER_BATCH` is clamped, not rejected.

### GET `/api/matches/{id}/me?playerId=&token=` -> 200
`{screen: "wait"|"play"|"end", team: "inter"|"gremio", matchStatus: "lobby"|"running"|"finished", result?}`
- LOBBY -> wait, RUNNING -> play, FINISHED -> end.
- `result` is present only when FINISHED. It is uppercase `INTER|GREMIO|DRAW`, matching the WS `ended` message (consumer.py). It is omitted otherwise (`response_model_exclude_none`).
- Same 401/403 rules as pulls. `matchStatus` is lowercase, like `/public`.

## Dedup
`Container.seen_batches` maps `"{matchId}:{batchId}"` to a monotonic expiry (`BATCH_DEDUP_TTL_S`). Expired keys are pruned on each pull. A repeat within the TTL returns 202 with no enqueue. The key is recorded before the awaited enqueue. There is no await between check and set, so there is no race in a single event loop. It is per-process (shortcut: swap for Redis when scaled). The consumer's `event_exists` check remains the durable dedup.

## Queued payload
`PullEvent(id=uuid4, match_id, player_id, team=<player's stored team, not client-supplied>, count=<clamped>, client_ts=body.clientTs, server_ts=now UTC (model default), batch_id=body.batchId)`.

## Notes for the frontend (Tasks 13/14)
- Any 2xx means the batch is safe to clear. A 409 means the match is over or not started, so stop flushing and poll `/me`.
- A retried batch with the same `batchId` is harmless.

## Deviations
- I wrote the implementation before the tests, so there was no red phase. All 9 new tests passed on first run.
- The tests set match status through `matches.update_match` and read the queue with `receive_batch`; no consumer runs.
