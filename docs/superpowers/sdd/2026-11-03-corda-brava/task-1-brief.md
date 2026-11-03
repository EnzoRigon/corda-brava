### Task 1: Backend skeleton — settings, app factory, domain entities & enums

**Files:**
- Create: `backend/app/core/settings.py`, `backend/app/core/app_factory.py`, `backend/app/core/logging.py`
- Create: `backend/app/domain/enums.py`, `backend/app/domain/entities.py`
- Create: `backend/pyproject.toml`, `backend/app/__init__.py` (+ package `__init__.py`s)
- Create: `backend/app/api/health.py` (GET `/health` → `{"status":"ok"}`)
- Test: `backend/tests/test_settings.py`, `backend/tests/test_health.py`

**Interfaces:**
- Produces: `Settings` (pydantic-settings BaseSettings) with every var in `prompt.md §4` typed with defaults; `get_settings()` cached accessor. `create_app(settings) -> FastAPI` app factory mounting `/health` and `/api` router root. Enums `MatchStatus{LOBBY,RUNNING,FINISHED}`, `Team{INTER,GREMIO}`, `MatchResult{INTER,GREMIO,DRAW}`, `EndReason{WIN,TIMEOUT}`, `BalanceMode{RAW,NORMALIZED}`, `QueueBackend{MEMORY,AZURE_SERVICE_BUS}`. Dataclass/Pydantic domain models `Match`, `Player`, `PullEvent`, `TickInput`, `MatchState` with fields per `prompt.md §11`.

- [ ] **Step 1:** Write `test_settings.py`: asserts defaults (`HOST_PASSWORD=="Inter>Gremio"`, `DEFAULT_MATCH_DURATION_S==120`, `ROPE_TARGET==100`, `TEAM_BALANCE_MODE=="normalized"`, `QUEUE_BACKEND=="memory"`) and that env override changes a value. Write `test_health.py`: `TestClient(create_app(...)).get("/health").json()=={"status":"ok"}`.
- [ ] **Step 2:** Run `pytest backend/tests/test_settings.py backend/tests/test_health.py -v` → FAIL (import errors).
- [ ] **Step 3:** Implement enums, domain entities, `Settings`, `get_settings`, `create_app`, `/health`. Configure `pyproject.toml` (deps: fastapi, uvicorn[standard], pydantic, pydantic-settings, pyjwt, httpx, pytest, pytest-asyncio, ruff, black).
- [ ] **Step 4:** Run the two tests → PASS.
- [ ] **Step 5:** Commit `feat(backend): skeleton — settings, app factory, domain entities, health`.

