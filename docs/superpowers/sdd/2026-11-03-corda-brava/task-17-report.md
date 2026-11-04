# Task 17 report: Dockerfiles + compose + .env.example

Commit: ac04463 (code). Docker is NOT installed here: `docker compose config/up/build` was **not run**.

## Files
- `backend/Dockerfile` (multi-stage python:3.11-slim, venv copied, non-root uid 10001, `/data` owned by app, HEALTHCHECK via python urllib on /health), `backend/.dockerignore`
- `frontend/Dockerfile` (stages: `dev` node:20-alpine with npm ci; `build` runs npm run build with VITE_* ARGs; final nginx:alpine), `frontend/nginx.conf`, `frontend/.dockerignore`
- `docker-compose.yml` (prod-shaped), `docker-compose.dev.yml` (override), `.env.example`
- `frontend/vite.config.ts`: proxy target now `process.env.VITE_PROXY_TARGET || "http://localhost:8000"` (local dev unchanged); `declare const process` avoids adding @types/node.
- `.gitignore`: added `.env`.

## Services / ports / volume
- `backend`: not published; port 8000 internal only. Volume `corda_data` -> `/data` (SQLite `sqlite:////data/corda_brava.db`).
- `frontend` (nginx): only published port, `${PUBLIC_PORT:-80}:80`; depends_on backend `service_healthy`; `restart: unless-stopped` on both.
- nginx: SPA fallback `try_files $uri /index.html`; `/api/*` and `/health` proxied to backend:8000 with Upgrade/Connection map, Host, X-Forwarded-For/Proto, read timeout 3600s.
- HOST_PASSWORD and SECRET_KEY use `${VAR:?...}`: compose fails if unset; nothing insecure baked in the image.
- Dev override: backend `--reload` with `./backend/app` bind-mounted over `/app/app`, port 8000 published; frontend uses `dev` target, Vite on 0.0.0.0:5173, `VITE_PROXY_TARGET=http://backend:8000`, source bind mount + anonymous node_modules volume, `ports: !override` so 80 is not published (needs Compose >= 2.24).

## Run
- Prod: `cp .env.example .env`, set HOST_PASSWORD, SECRET_KEY, PUBLIC_BASE_URL (http://<LAN-IP>), VITE_PUBLIC_BASE; `docker compose up -d --build`; open http://<LAN-IP>.
- Dev: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`; Vite at :5173, API at :8000.

## Single worker
uvicorn runs with one worker: MatchRegistry, in-memory queue and batch dedup are per-process; multiple workers would split state.

## Proxy-IP decision
Login rate limiter keys on `request.client.host`. Behind nginx that would be the nginx IP for everyone (shared lockout). Fix without code change: uvicorn `--proxy-headers --forwarded-allow-ips=*` (client IP taken from X-Forwarded-For). Safe because the backend is unpublished (only nginx can reach it). No Python change, so no new test.

## Verified
- Backend pytest 144 passed, ruff and black clean.
- Frontend: vitest 49 passed, tsc --noEmit, build, lint clean.
- Both compose YAMLs parse (PyYAML, with !override tag registered). Every Settings field appears in .env.example (scripted grep). nginx.conf re-read by eye.

## NOT verified
Docker build, `compose config`, `compose up`, healthcheck, nginx syntax (`nginx -t`), WS through proxy, `!override` support. Task 18 / a Docker machine must run these.

## Deviations
- No `docker compose config/up` (steps 2-4 of brief) due to no Docker.
- Frontend Dockerfile has an extra `dev` stage reused by the dev override.
- Compose `env_file: .env` is required to exist (copy .env.example).
