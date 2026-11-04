# Corda Brava

> **Corda Brava** ("fierce rope") — a themed, mobile-join **tug-of-war party game**: **Inter** (red) vs **Grêmio** (blue/black). A host opens a big screen and shows a QR code; players scan it on their phones, pick a team, and spam a **PUXAR** button. Every tap tugs a rope live on the host screen between two pixel-art mascots. First team to drag the rope fully to their side wins; if time runs out it's a draw (*empate*). The host screen then shows a celebration + analytics.

This is a **private / educational fan project** (a party game), **not** a commercial product. All player-facing copy is **Brazilian Portuguese (PT-BR)**; code, identifiers, and comments are English.

---

## Status (work in progress)

Being built task-by-task from the spec in [`prompt.md`](./prompt.md), following the plan in
[`docs/superpowers/plans/2026-11-03-corda-brava.md`](./docs/superpowers/plans/2026-11-03-corda-brava.md).

**Done so far (backend, Phase A — complete):**

| Task | What | State |
|------|------|-------|
| 1 | Backend skeleton — settings, app factory, domain entities & enums, `/health` | ✅ reviewed |
| 2 | Pure game rules (`apply_pulls` / `check_win` / `resolve_result`) + tests | ✅ reviewed |
| 3 | Repository interfaces + SQLite impls (WAL, unique constraints) + tests | ✅ reviewed |
| 4 | Broker-shaped `EventQueue` + in-memory lease/ack/redelivery + tests | ✅ reviewed |
| 5 | Host auth — password check, JWT host token, `require_host`, WS token verify + tests | ✅ reviewed |
| 6 | Match state machine + single-writer consumer loop (atomic apply, poison-safe) + registry + tests | ✅ reviewed |
| 7 | Analytics service (§15 payload: timeline, peak, best/worst, %, leaderboard) + tests | ✅ reviewed |
| 8 | Player API — public info + join (one-per-device idempotent), player token, DI container + tests | ✅ reviewed |
| 9 | Pull ingest (202, batchId dedup, clamp) + `/me` player screen + tests | ✅ reviewed |
| 10 | Host routes + host WebSocket (snapshot/tick/ended), lifespan wiring, login rate limit + tests | ✅ reviewed |
| 11 | Frontend skeleton — Vite + React + TS, routing, theme, pixel font, typed API client, `useDeviceId` | ✅ reviewed |
| 12 | Owner mascot/crest files copied verbatim + `Mascot`/`Crest` display components | ✅ reviewed |
| 13 | `usePullBuffer` — batched taps, same-batchId retry, clamp, flush-on-hide (sendBeacon) | ✅ reviewed |
| 14 | Player flow — Join → Wait → Play (PUXAR) → End, `/me` polling, session restore on reload | ✅ reviewed |
| 15 | `useHostSocket` + host Login / Create / Lobby (QR, animated roster) | ✅ reviewed |
| 16 | Host match rope scene (interpolated knot, timer) + results with analytics charts | ✅ reviewed |
| 17 | Dockerfiles + single-port compose (nginx proxy, SQLite volume) + dev override + `.env.example` | ✅ reviewed (Docker runtime not yet run) |

**Current test count:** 144 passing (backend), 49 passing (frontend), 1 Playwright e2e. Lint (ruff + black) clean.

**All 18 tasks are built.** Task 18 added the READMEs and a Playwright end-to-end flow (green against the Vite dev stack). Docker (`docker compose up`) has **not** been run: Docker was unavailable in the build environment. See the [progress ledger](./docs/superpowers/sdd/2026-11-03-corda-brava/progress.md) for details.

---

## Repository layout

```
/
├── prompt.md                  # the authoritative spec (what to build) — leave as-is
├── backend/                   # FastAPI backend (Python 3.11+)
│   ├── app/
│   │   ├── core/              # settings, app factory, logging
│   │   ├── domain/            # entities, enums, PURE game rules (no IO/framework)
│   │   ├── repositories/      # repo interfaces + SQLite impls (WAL, behind Protocols)
│   │   └── queue/             # broker-shaped EventQueue + in-memory impl + factory
│   ├── tests/                 # pytest (domain rules, repos, queue, settings, health)
│   └── pyproject.toml
├── frontend/                  # React 18 + Vite + TS (host + player screens)
├── docs/
│   ├── logo-references/        # owner-authored pixel-art club crests (inter.png, gremio.png)
│   ├── mascot-references/       # owner-authored mascot references + ready-made sprite assets
│   │   └── mascot-test/assets/  # saci_*.gif/png, mosq_*.gif/png  (the sprites the game will use)
│   └── superpowers/
│       ├── specs/              # design doc (decisions layered on the spec)
│       ├── plans/              # the task-by-task implementation plan
│       └── sdd/                # progress ledger + per-task briefs/reports/review diffs
└── README.md / CLAUDE.md
```

---

## Running it

### Local dev (two terminals, or `.claude/launch.json` configs `backend` + `frontend`)

```bash
# backend (see backend/README.md): venv + pip install -e .
cd backend && uvicorn app.core.app_factory:create_app --factory --reload   # :8000
# frontend
cd frontend && npm install && npm run dev                                   # :5173, proxies /api + WS
```

Open http://localhost:5173/host/login. Default host password: see `HOST_PASSWORD` in settings / `.env.example`.

### Docker (prod, single port)

```bash
cp .env.example .env        # set HOST_PASSWORD and SECRET_KEY (python -c "import secrets; print(secrets.token_hex(32))")
docker compose up -d --build
# open http://<host>/        (nginx serves the SPA and proxies /api + WS; SQLite lives on a named volume)
```

### Docker (dev, hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build   # needs Compose >= 2.24
```

### LAN play / QR code

Phones cannot open `localhost`. Set `PUBLIC_BASE_URL` and `VITE_PUBLIC_BASE` in `.env` to `http://<LAN-IP>` (add `:PORT`
if `PUBLIC_PORT` is not 80) before building, so the QR points at an address phones can reach.

### Host and player flow

1. Host opens `/host/login`, enters the password, picks duration (30-600 s) and scoring, and creates a match.
2. The lobby shows a QR code and live roster. Players scan it (`/j/<matchId>`), enter a name, pick Inter or Grêmio
   (one player per device).
3. Host clicks **Iniciar partida**. Players tap **PUXAR**; the rope moves live on the host screen.
4. The match ends when a team drags the rope to its side, or on timeout (draw). Players see a result screen;
   the host sees a banner, charts and a leaderboard, and can start **Nova Partida**.

### End-to-end test

With the stack running: `cd frontend && npx playwright install chromium && npm run e2e` (details in
`frontend/README.md`; `E2E_BASE_URL=http://localhost` targets the Docker stack).

### Swapping to Azure Service Bus

The queue is broker-shaped (async, leased receive, explicit ack, at-least-once, idempotent by `batchId`). To move off
the in-memory queue:

1. Add one file, `backend/app/queue/azure_service_bus.py`, with `AzureServiceBusEventQueue` implementing the
   `EventQueue` Protocol (`start`, `close`, `enqueue`, `receive_batch`, `ack`, `abandon`) on the `azure-servicebus` async SDK.
2. Add its `elif` branch in `backend/app/queue/factory.py`.
3. Set `QUEUE_BACKEND=azure_service_bus`, `AZURE_SERVICEBUS_CONNECTION_STRING` and `AZURE_SERVICEBUS_QUEUE_NAME`.

No consumer, service or domain changes are needed. Until the adapter exists the factory raises `NotImplementedError`.

### VPS, TLS and wss

Run the Docker stack on the VPS and put a TLS-terminating reverse proxy (Caddy, Traefik, or nginx + certbot) in front of
port 80, forwarding to it with WebSocket upgrade headers. Set `PUBLIC_BASE_URL` and `VITE_PUBLIC_BASE` to
`https://<your-domain>`. WebSocket and API URLs derive from the page origin, so they become `wss://` / `https://`
automatically; leave `VITE_API_BASE` / `VITE_WS_BASE` empty. Restrict `CORS_ORIGINS` from `*` to your origin.

### Scaling limitation

Run **one process, one worker**. The in-memory queue, match registry and batch dedup are per-process, so multiple
workers or replicas would split a match's state. Scaling out needs the Azure queue plus shared state, which is out of scope.

---

## Key design decisions (so far)

- **Rope convention:** `rope ∈ [-ROPE_TARGET, +ROPE_TARGET]`, `0` = center. Negative = Inter (left), positive = Grêmio (right).
- **Scoring:** `normalized` by default (per-player intensity, fair for uneven teams); `raw` selectable via env. Formulas in `backend/app/domain/rules.py`, unit-tested.
- **Queue is broker-shaped:** async, leased `receive_batch`, explicit `ack`, genuine at-least-once redelivery of unacked batches. The in-memory impl honors that contract today; swapping to Azure Service Bus later is "add one `AzureServiceBusEventQueue` adapter file + flip `QUEUE_BACKEND`" with no consumer/service/domain changes.
- **SQLite behind repository Protocols:** no sqlite types leak past the repo boundary; WAL mode; writes serialized through a single lock.
- Full rationale: [`docs/superpowers/specs/2026-11-03-corda-brava-design.md`](./docs/superpowers/specs/2026-11-03-corda-brava-design.md).

---

## Art & assets policy (important)

The two mascots — Inter's **Saci** and Grêmio's **Mosqueteiro** — and the club crests are **image files authored and committed by the project owner** (under `docs/mascot-references/.../assets/` and `docs/logo-references/`). The application **copies and displays those files**; **no code draws, generates, or renders the club mascots or crests**. This keeps the project self-contained with the owner's own assets and avoids any code-level reproduction of the characters. If you extend the art, add original assets or original characters — do not write code that renders the club mascots/crests.

---

## How this project is being built

Work is executed **task-by-task via dispatched subagents** (plan → implement → review → fix-loop → commit), tracked in the SDD progress ledger. If you're picking this up in a new session, read **`CLAUDE.md`** next — it explains exactly how to resume and keep the docs/ledger current.
