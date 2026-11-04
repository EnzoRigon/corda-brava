# Corda Brava — backend

FastAPI + SQLite (WAL). Python 3.11+ (developed on 3.14).

## Run

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows (Git Bash); on Linux/macOS: . .venv/bin/activate
pip install -e .
pip install pytest pytest-asyncio ruff black
uvicorn app.core.app_factory:create_app --factory --reload   # http://localhost:8000/health
```

## Test and lint

```bash
python -m pytest -q
python -m ruff check . && python -m black --check .
```

## Settings

Environment-driven via `pydantic-settings` (`app/core/settings.py`); a `.env` file or process env. Every variable
is documented in the root [`.env.example`](../.env.example). Key ones: `HOST_PASSWORD`, `SECRET_KEY` (required in
production), `PUBLIC_BASE_URL` (origin phones open from the QR), `DATABASE_URL`, `ROPE_TARGET`, `TEAM_BALANCE_MODE`
(`normalized`|`raw`), `LATE_JOIN_POLICY`, `QUEUE_BACKEND` (`memory`|`azure_service_bus`).

## Layout

```
app/core/          settings, app factory (lifespan wiring), logging
app/domain/        entities, enums, pure game rules (no IO)
app/repositories/  repository Protocols + SQLite implementations
app/queue/         broker-shaped EventQueue, in-memory impl, factory
app/services/      match state machine, consumer loop, registry, analytics
app/api/           player + host REST routes, host WebSocket
tests/             pytest
```

Single-process by design: the in-memory queue, match registry and batch dedup are per-process (see the root README).
