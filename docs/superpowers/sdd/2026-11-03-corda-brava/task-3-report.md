# Task 3 Report: Repository Interfaces + SQLite Implementations

## Status: COMPLETE

---

## Protocol Signatures (verbatim)

### interfaces.py — `app.repositories.interfaces`

```python
class UniqueConstraintError(Exception):
    """Raised when a repository INSERT would violate a UNIQUE constraint.
    Wraps the underlying sqlite3.IntegrityError so callers do not need
    to import sqlite3 directly.  The original error is stored in __cause__.
    """

class MatchRepository(Protocol):
    def create_match(self, match: Match) -> Match: ...
    def get_match(self, match_id: str) -> Match | None: ...
    def update_match(self, match: Match) -> Match: ...

class PlayerRepository(Protocol):
    def add_player(self, player: Player) -> Player: ...
    def get_player(self, player_id: str) -> Player | None: ...
    def get_player_by_device(self, match_id: str, device_id: str) -> Player | None: ...
    def list_players(self, match_id: str) -> list[Player]: ...

class EventRepository(Protocol):
    def add_event(self, event: PullEvent) -> None: ...
    def event_exists(self, match_id: str, batch_id: str) -> bool: ...
    def list_events(self, match_id: str) -> list[PullEvent]: ...
```

---

## UniqueConstraintError

- **Location**: `app.repositories.interfaces.UniqueConstraintError` (inherits `Exception`)
- **Raised by**: `SQLitePlayerRepository.add_player` when `sqlite3.IntegrityError` is caught
- **Stored cause**: original `sqlite3.IntegrityError` in `__cause__`
- **Callers never need to import sqlite3**: the error boundary is the repository implementation

---

## add_event Duplicate Behaviour

**Choice: INSERT OR IGNORE (silent no-op)**

Rationale: The ingest endpoint is the hot path. Using `INSERT OR IGNORE` keeps the call non-throwing and avoids any lock/exception overhead on duplicates. Callers that need to detect dedup (e.g. analytics) call `event_exists()` first. The `UNIQUE (match_id, batch_id)` constraint remains in the schema and is enforced at the DB level.

`add_player` uses the opposite policy (raise on duplicate) because the service layer (Task 8) must decide how to handle rejoin — it calls `get_player_by_device` first.

---

## Datetime Storage Format

All `datetime` columns stored as **ISO-8601 text with UTC offset** (e.g. `"2024-06-01T12:00:00+00:00"`).

- Produced by: `datetime.isoformat()` (Python's standard method)
- Consumed by: `datetime.fromisoformat(text)` (Python 3.11+ parses offset-aware ISO strings)
- Result: timezone-aware `datetime` with `tzinfo=UTC` on every round-trip
- No epoch integer arithmetic, no loss of timezone information

---

## WAL Mode + Write Lock Approach

**File**: `app.repositories.sqlite.connection`

- `get_connection(db_path)` opens a shared `sqlite3.Connection` with `check_same_thread=False`
- Immediately executes `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`
- One connection is cached per `db_path` string (module-level `dict`)
- A module-level `threading.Lock` (`_WRITE_LOCK`) is held via the `write_lock()` context manager for all INSERT/UPDATE/DELETE operations
- Reads execute without acquiring the lock (WAL allows concurrent readers)
- This matches the spec in §12: "wrap writes in a lock"

---

## Files Created

```
backend/
  app/repositories/
    __init__.py
    interfaces.py
    sqlite/
      __init__.py
      connection.py    # WAL, lock, connection cache
      bootstrap.py     # CREATE TABLE IF NOT EXISTS, indexes, constraints
      match_repo.py    # SQLiteMatchRepository
      player_repo.py   # SQLitePlayerRepository
      event_repo.py    # SQLiteEventRepository
  tests/repositories/
    __init__.py
    test_sqlite_repos.py  # 17 tests
```

---

## Schema Summary (bootstrap.py)

| Table         | PK  | UNIQUE constraint          | Index                          |
|---------------|-----|----------------------------|--------------------------------|
| `matches`     | id  | —                          | —                              |
| `players`     | id  | (match_id, device_id)      | —                              |
| `pull_events` | id  | (match_id, batch_id)       | (match_id, server_ts) ASC      |

MatchConfig stored inline on `matches` (19 columns total) — no join needed for reads.

---

## Test Output

```
======================== 60 passed, 1 warning in 0.40s =========================
```

- 17 new repository tests (all pass)
- 43 pre-existing tests still green (Tasks 1+2 domain rules, health, settings)
- ruff: All checks passed
- black: All files unchanged

---

## Commit

`feat(repos): repository interfaces + SQLite impls (WAL, unique constraints) + tests`
