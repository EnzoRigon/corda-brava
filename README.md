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

**Current test count:** 144 passing (backend), 7 passing (frontend). Lint (ruff + black) clean.

**Backend (Phases A + B) complete.** **Not yet built:** rest of Phase C (Tasks 13–16: pull buffer, player + host pages); Phase D Docker + READMEs-for-run + end-to-end. See the plan for the full list and the [progress ledger](./docs/superpowers/sdd/2026-11-03-corda-brava/progress.md) for exactly where things stand.

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
├── frontend/                  # React 18 + Vite + TS  (NOT YET BUILT — Phase C)
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

## Running the backend (dev)

Requires Python 3.11+ (developed on 3.14).

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
pip install pytest pytest-asyncio ruff black   # dev tools

# run the tests
python -m pytest -v

# run the API (health check only until the routers land)
uvicorn app.core.app_factory:create_app --factory --reload
# then: curl http://localhost:8000/health  ->  {"status":"ok"}
```

Configuration is environment-driven via `pydantic-settings` (`backend/app/core/settings.py`); defaults match `prompt.md` §4. A root `.env.example` documenting every variable lands in Phase D.

> The full `docker compose up` single-port stack, the frontend, and the LAN/QR run instructions are specified in `prompt.md` §4b / §16–§18 and will be filled in as those phases are built.

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
