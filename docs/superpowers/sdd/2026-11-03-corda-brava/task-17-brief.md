### Task 17: Dockerfiles + compose (prod single-port proxy + volume) + dev override + .env.example

**Files:**
- Create: `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` (SPA fallback + `/api` & WS proxy) OR `proxy/` service config, `docker-compose.yml`, `docker-compose.dev.yml`, `.env.example`, `.dockerignore`s
- Test: scripted smoke (in Task 18 loop): `docker compose up -d` then `curl /health`, `curl /` 200.

**Interfaces:**
- Produces: multi-stage backend image (python:3.11-slim, non-root, Uvicorn **single worker**, HEALTHCHECK `/health`); multi-stage frontend (npm ci && build → nginx serving static + SPA fallback + proxying `/api` and WS upgrade headers to backend); base compose = production-shaped (single public port 80, named volume for SQLite, `restart: unless-stopped`, `depends_on` healthcheck); dev override = bind mounts, Uvicorn `--reload`, Vite dev, exposed ports; `.env.example` documents **every** var from `prompt.md §4` incl. `VITE_PUBLIC_BASE`, `SECRET_KEY`, `HOST_PASSWORD` (overridable, no insecure baked value).

- [ ] **Step 1:** Write Dockerfiles, nginx conf (correct `Upgrade`/`Connection` for WS), both compose files, `.env.example`.
- [ ] **Step 2:** `docker compose config` validates both files.
- [ ] **Step 3:** `docker compose up -d --build`; `curl -f localhost/health` and `curl -f localhost/` → 200; data volume present.
- [ ] **Step 4:** `docker compose down`.
- [ ] **Step 5:** Commit `chore(docker): Dockerfiles + prod/dev compose (single port, proxy, volume) + .env.example`.

