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
(`normalized`|`raw`), `LATE_JOIN_POLICY`, `QUEUE_BACKEND` (`memory`|`azure_service_bus`). The app reads
`backend/.env` only, wherever it is started; the repo-root `.env` belongs to Docker Compose and is not read, so a dev
server never picks up the Docker values. For `azure_service_bus` also set `AZURE_SERVICEBUS_CONNECTION_STRING` and
`AZURE_SERVICEBUS_QUEUE_NAME` (in `backend/.env` for a local run; use a queue of its own, not the Docker stack's), then
create or check the queue with `python -m app.queue.provision`, which also reads the root `.env` (see the root
README, "Azure Service Bus").

## Layout

```
app/core/          settings, app factory (lifespan wiring), logging
app/domain/        entities, enums, pure game rules (no IO)
app/repositories/  repository Protocols + SQLite implementations
app/queue/         broker-shaped EventQueue, in-memory + Azure Service Bus impls, factory, provision
app/services/      match state machine, consumer loop, registry, analytics
app/api/           player + host REST routes, host WebSocket
tests/             pytest
```

Single-process by design: the in-memory queue, match registry and batch dedup are per-process (see the root README).
