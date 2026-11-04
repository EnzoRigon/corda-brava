# Task 6 Report — MatchService + ConsumerLoop + MatchRegistry

**Status:** DONE. Commit 2b366c7. 86 tests pass (78 prior + 8 new), ruff and black clean.

## Files
- `backend/app/services/match_service.py` (service, `ConflictError`, `MatchNotFoundError`)
- `backend/app/services/consumer.py` (`ConsumerLoop`, `utcnow`)
- `backend/app/services/registry.py` (`MatchRegistry`, `Broadcast` type)
- `backend/tests/services/test_consumer.py` (4 tests, also holds the shared `Env` helper)
- `backend/tests/services/test_match_service.py` (4 tests)

## Public signatures
```python
class ConflictError(Exception)        # -> HTTP 409
class MatchNotFoundError(Exception)   # -> HTTP 404

MatchService(*, matches, players, events, queue, registry, settings, clock=utcnow)
  create_match(duration_s: int | None = None) -> Match      # ValueError if outside MIN/MAX
  get_match_view(match_id) -> MatchState                    # remaining_s computed from clock
  update_duration(match_id, duration_s) -> Match            # ConflictError unless LOBBY
  start(match_id) -> Match                                  # sync; LOBBY->RUNNING; needs a running asyncio loop
  async cancel(match_id) -> Match                           # stops loop; unfinished -> FINISHED, result None

ConsumerLoop(match_id, *, matches, players, events, queue, settings, broadcast, clock=utcnow)
  async run() -> None        # ticks every TICK_INTERVAL_MS until FINISHED
  async tick() -> bool       # one tick; True when finished

MatchRegistry()
  add_listener(match_id, cb) / remove_listener(match_id, cb)
  async broadcast(match_id, payload)   # failing listener is dropped
  is_running(match_id) -> bool
  start_loop(match_id, coro) / async stop_loop(match_id)

Broadcast = Callable[[dict[str, Any]], Awaitable[None]]
```

## Broadcast payloads (prompt.md section 14 shapes)
- Every tick: `{"type":"tick","rope":float,"remainingS":float,"delta":{"inter":int,"gremio":int},"scores":{"inter":{"pulls":int},"gremio":{"pulls":int}}}`
- On finish, after the final tick: `{"type":"ended","result":"INTER|GREMIO|DRAW","endReason":"win|timeout","finalRope":float}`. No `analytics` yet; Task 10 should add it in the WS layer.

## Start / stop
`MatchService.start` persists RUNNING, `started_at`, `ends_at`, then `registry.start_loop(id, loop.run())`. The loop ends itself on win or timeout. `cancel` calls `registry.stop_loop` (task.cancel). The service wires the broadcast to `registry.broadcast(match_id, ...)`; WS handlers call `registry.add_listener`.

## Behavior notes
- Ack happens only after `update_match`. Duplicate batch_ids (found via `event_exists`) are skipped but still acked.
- The queue is global. Messages for other matches are abandoned. Queue receive uses `max_wait_s=0`, and pacing is `asyncio.sleep`.
- Scores are kept in the loop and seeded from `list_events` on construction.
- Tests drive `tick()` with a fake clock; only the win test uses `run()` with `TICK_INTERVAL_MS=1`.

## Deviations
- Single `cancel` instead of separate reset/cancel; "new match" is a new `create_match`.
- `add_event` with an unknown player_id raises an FK error that would kill the loop. Task 8 must validate players at ingest.
- `create_match` takes an optional duration and validates against MIN/MAX.
- Tests were written together with the code, so the red step was not run separately.
