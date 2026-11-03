# Task 1 Report — Backend Skeleton

**Status:** DONE  
**Commit:** `5da5194`  
**Tests:** 8 passed, 0 failed (`cd backend && python -m pytest tests/test_settings.py tests/test_health.py -v`)  
**Linters:** `ruff check .` → All checks passed; `black --check .` → all unchanged

---

## Files Created

```
backend/
├── .gitignore
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py          ← GET /health → {"status":"ok"}
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app_factory.py     ← create_app(settings) -> FastAPI
│   │   ├── logging.py         ← configure_logging()
│   │   └── settings.py        ← Settings (pydantic-settings) + get_settings()
│   └── domain/
│       ├── __init__.py
│       ├── entities.py        ← Match, Player, PullEvent, TickInput, MatchState
│       └── enums.py           ← MatchStatus, Team, MatchResult, EndReason, BalanceMode, QueueBackend
└── tests/
    ├── __init__.py
    ├── test_health.py
    └── test_settings.py
```

---

## Enum Signatures (`backend/app/domain/enums.py`)

All enums are `StrEnum` — values are lowercase strings, which serialise cleanly to/from JSON and SQLite text columns.

```python
class MatchStatus(StrEnum):
    LOBBY    = "lobby"
    RUNNING  = "running"
    FINISHED = "finished"

class Team(StrEnum):
    INTER  = "inter"
    GREMIO = "gremio"

class MatchResult(StrEnum):
    INTER  = "inter"
    GREMIO = "gremio"
    DRAW   = "draw"

class EndReason(StrEnum):
    WIN     = "win"
    TIMEOUT = "timeout"

class BalanceMode(StrEnum):
    RAW        = "raw"
    NORMALIZED = "normalized"

class QueueBackend(StrEnum):
    MEMORY             = "memory"
    AZURE_SERVICE_BUS  = "azure_service_bus"
```

---

## Entity Signatures (`backend/app/domain/entities.py`)

All entities are Pydantic v2 `BaseModel` — framework/IO-free (no FastAPI or SQLite imports).

### `TeamConfig`
```python
class TeamConfig(BaseModel):
    id: str               # e.g. "inter" | "gremio"
    name: str             # display name
    primary_color: str    # hex color
    secondary_color: str  # hex color
```

### `MatchConfig`
```python
class MatchConfig(BaseModel):
    duration_s: int
    rope_target: int
    balance_mode: BalanceMode
    inter: TeamConfig
    gremio: TeamConfig
```

### `Match`
```python
class Match(BaseModel):
    id: str
    status: MatchStatus = MatchStatus.LOBBY
    created_at: datetime = Field(default_factory=datetime.utcnow)
    config: MatchConfig
    rope_position: float = 0.0
    started_at: datetime | None = None
    ends_at: datetime | None = None
    result: MatchResult | None = None
    end_reason: EndReason | None = None
```

### `Player`
```python
class Player(BaseModel):
    id: str
    match_id: str
    device_id: str
    name: str
    team: Team
    token: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)
```

### `PullEvent`
```python
class PullEvent(BaseModel):
    id: str
    match_id: str
    player_id: str
    team: Team
    count: int
    client_ts: float      # unix timestamp from client
    server_ts: datetime = Field(default_factory=datetime.utcnow)
    batch_id: str         # client UUID for idempotency/dedup
```

### `TickInput`
```python
class TickInput(BaseModel):
    pulls_inter: int = 0
    pulls_gremio: int = 0
    players_inter: int = 0    # active player count — needed for normalized scoring
    players_gremio: int = 0
```

### `MatchState`
```python
class MatchState(BaseModel):
    match_id: str
    status: MatchStatus
    rope_position: float
    started_at: datetime | None = None
    ends_at: datetime | None = None
    remaining_s: float | None = None
    result: MatchResult | None = None
    end_reason: EndReason | None = None
```

---

## Settings Defaults (`backend/app/core/settings.py`)

Key fields verified by tests:

| Var | Default |
|-----|---------|
| `HOST_PASSWORD` | `"Inter>Gremio"` |
| `DEFAULT_MATCH_DURATION_S` | `120` |
| `ROPE_TARGET` | `100` |
| `TEAM_BALANCE_MODE` | `"normalized"` |
| `QUEUE_BACKEND` | `"memory"` |
| `HOST_TOKEN_TTL_SECONDS` | `21600` |
| `TICK_INTERVAL_MS` | `500` |
| `PULL_UNIT` | `1.0` |
| `MAX_PULLS_PER_BATCH` | `200` |
| `BATCH_DEDUP_TTL_S` | `30` |
| `LATE_JOIN_POLICY` | `"block"` |
| `QUEUE_LEASE_TIMEOUT_S` | `10` |
| `CORS_ORIGINS` | `"*"` |
| `DATABASE_URL` | `"sqlite:///./corda_brava.db"` |
| `SECRET_KEY` | `secrets.token_hex(32)` (random dev default) |

`get_settings()` is an `lru_cache(maxsize=1)` accessor. Clear with `get_settings.cache_clear()` in tests.

---

## `create_app` signature

```python
def create_app(settings: Settings) -> FastAPI
```

- Calls `configure_logging()`.
- Adds `CORSMiddleware` from `settings.CORS_ORIGINS` (wildcard or comma-separated).
- Mounts `health_router` at root (GET `/health`).
- Creates and mounts an empty `/api` `APIRouter` (later tasks attach sub-routers).

---

## Decisions

1. **StrEnum (not `str + Enum`)**: Python 3.11+ ships `StrEnum` in stdlib — cleaner than the older mixin pattern. All enum values are lowercase strings; `Team.INTER == "inter"` is true.

2. **Pydantic BaseModel for entities**: Consistent with schemas/settings; enables `.model_dump()`, `.model_validate()`, and type-safe field access across all layers without extra adapters.

3. **`pyproject.toml` build backend**: `setuptools.build_meta` (not the legacy `backends.legacy:build` path which does not exist in all setuptools versions). `pythonpath = ["."]` in `[tool.pytest.ini_options]` keeps the import path clean without a `src/` layout.

4. **Python 3.14 venv**: The system Python on this machine is 3.14 (the constraint is >=3.11, so 3.14 is fine). All code is compatible.

5. **`Optional[X]` → `X | None`**: Ruff UP045 auto-fixed during lint — code is consistent with Python 3.10+ union syntax.

---

## Concerns

- **httpx + starlette `TestClient` deprecation warning**: `starlette.testclient` recommends installing `httpx2` (a fork) over `httpx`. This is a minor warning from the version installed (fastapi-0.162 / starlette-1.10) and does not affect test correctness. Later tasks should track whether upgrading to a stable FastAPI/starlette release resolves this without introducing breaking changes.
- **`SECRET_KEY` default**: Generates a fresh random key at startup if not set. This means JWTs are invalidated on every restart in dev if the env var is not set. Documented in settings comment; should be pinned in `.env` before any real use.

---

## Fix Report — Review Finding (commit `05d2c1d`)

**Finding:** Three `Field(default_factory=datetime.utcnow)` calls in `entities.py` used the deprecated `datetime.utcnow()` (deprecated Python 3.12+; this venv runs 3.14).

**Fix applied to `backend/app/domain/entities.py`:**

| Field | Before | After |
|-------|--------|-------|
| `Match.created_at` | `datetime.utcnow` | `lambda: datetime.now(tz=UTC)` |
| `Player.joined_at` | `datetime.utcnow` | `lambda: datetime.now(tz=UTC)` |
| `PullEvent.server_ts` | `datetime.utcnow` | `lambda: datetime.now(tz=UTC)` |

Import changed from `from datetime import datetime` → `from datetime import UTC, datetime` (ruff UP017 auto-fixed `timezone.utc` → `UTC` alias, available since Python 3.11).

**Verification:**
- `grep -r "utcnow" backend/app/domain/` → no output (clean)
- `cd backend && python -m pytest tests/ -v` → **8 passed**, 1 warning (starlette/httpx deprecation — pre-existing, unrelated)
- `ruff check .` → All checks passed
- `black --check .` → 13 files unchanged
