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

