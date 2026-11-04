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

