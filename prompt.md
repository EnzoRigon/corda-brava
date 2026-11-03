# Build "Corda Brava" — A Themed Tug-of-War Party Game

> **Game name:** `Corda Brava` ("fierce rope", a PT-BR play on *puxar a corda*) is the default. Alternatives you may use instead: **Puxa-Puxa**, **Cabo de Guerra Brabo**, **Corda Viva**. Pick one and use it consistently.

This document is a complete, execution-ready specification. Build the whole thing. Where a detail is left open, choose the option that best serves clean architecture and a fun, polished experience, and record the choice in the README. All **player-facing copy is in Brazilian Portuguese (PT-BR)**; code, identifiers, comments, and this spec are in English.

---

## 0. TL;DR of the Experience

A **host** opens a big screen, logs in with a password, creates a match, and shows a **QR code**. Players scan it on their phones, enter a name, pick a team (**Inter** red vs **Grêmio** blue/black), and wait. The host starts the match. Each player spams a **"PUXAR"** button; every tap tugs a rope toward their team. The rope moving is shown live on the host screen with two pixel-art mascots straining on a rope and a countdown timer. First team to drag the rope fully to their side **wins**; if time expires, it's a **draw (empate)**. The host screen then shows a celebration (happy winner mascot / crying loser mascot) plus rich **analytics**. A button starts a new match.

---

## 1. Theme, Mascots & Asset Policy (read first)

This is a **themed fan project for private / educational / internal use** (a party game), **not** a commercial product. The two teams are **SC Internacional ("Inter")** and **Grêmio FBPA ("Grêmio")**, and the game must faithfully depict their classic mascots so players instantly recognize who is who.

**Faithful mascots (required).** Reproduce both mascots **recognizably and cleanly in pixel-art**, including their team crests on the chest. Reference photos were provided by the project owner; match silhouette, colors, and signature props closely.

- **Inter — the "Saci" mascot:** a cheerful Black boy with a short afro, wearing a **red Phrygian cap (touca/gorro vermelho)** with a little bend at the tip, Inter's **red football jersey bearing the round white "SC Internacional" crest** on the chest, **white shorts with red trim**, white socks, and black football cleats. Personality: proud, energetic, playful. (In reference art he appears flexing his biceps, or standing hand-on-hip with a whistle/apito.)
- **Grêmio — the "Mosqueteiro" (Musketeer) mascot:** a classic Three-Musketeers figure with a **large blue plumed hat (chapéu azul com pena branca)**, black moustache + goatee, a **light-blue-and-white tabard/tunic displaying the round Grêmio crest** on the chest, holding a **thin fencing sword (florete/espada)** raised in one hand, brown gloves, dark boots. Personality: swashbuckling, confident, flamboyant.

**Colors (theme tokens):** Inter = red (`#E5050F`-ish) + white (+ dark details). Grêmio = blue (`#0D80BF` / lighter `#4FA9DC`) + white + black. Tune for contrast/aesthetics; keep them as central theme tokens.

**How to build the art — CSS/SVG by code (required):** author the mascots as **hand-crafted pixel-art in code** — a generated pixel grid rendered as SVG `<rect>` cells, or layered SVG/CSS shapes with `image-rendering: pixelated`, or a code-generated spritesheet. The art must be **self-contained in the repo** (committed source), **no external image downloads, no hotlinked/CDN art, no copyrighted files pulled from the web.** You are reproducing the characters *as original pixel-art renditions in code*, not embedding official image files.

**Fidelity bar:** a Grêmio or Inter fan glancing at the host screen should immediately and correctly identify each mascot. Keep them crisp, polished, consistent in pixel scale, and cohesive with the retro-arcade look. If a chosen skill/library helps produce pixel-art cleanly (see "Skills & tooling" note below), you may use it, as long as the output stays self-contained and faithful.

**Mascot animation states (both characters must support):** `idle` (gentle bob/breath), `straining` (leaning back, pulling the rope, effort on the face — used during the match, intensity can scale with how hard their team is pulling), `winning` (celebrating/arms up), `losing` (dragged forward, struggling), `happy` (big celebration — winner end screen), `crying` (very sad, tears, slumped in the corner — loser end screen). For a **draw**, both show a neutral exhausted/standoff pose.

**Reference images (in this repo):** faithful reference photos of both mascots are committed at **`docs/mascot-references/`**:
> - `00-both-mascots.png` — both side by side (Inter red vs Grêmio blue)
> - `01-inter-saci-flexing.png`, `02-inter-saci-whistle.png` — Inter "Saci"
> - `03-gremio-mosqueteiro-smoke.png`, `04-gremio-mosqueteiro-classic.png` — Grêmio "Mosqueteiro"
>
> Study these before drawing. Match the silhouette, palette, hat/cap, crest placement, and signature prop (Saci's cap + whistle; Mosqueteiro's plumed hat + sword). These are references for reproduction in code, not files to ship.

> **Skills & tooling note for the implementer:** before hand-rolling everything, check whether an available skill or small open-licensed tool/library can help generate faithful pixel-art sprites or convert the reference silhouettes into a clean pixel grid — use it only if the result is self-contained in the repo and license-clean. Otherwise author the SVG/CSS pixel-art directly. Either way, the two mascots and their crests must be faithful and instantly identifiable.

---

## 2. Repository Layout

```
/
├── backend/
│   ├── app/
│   │   ├── core/          # settings, app factory, logging, security
│   │   ├── domain/        # entities, enums, pure game rules (no IO/framework)
│   │   ├── repositories/  # repo interfaces + SQLite implementations
│   │   ├── queue/         # EventQueue interface + in-memory impl
│   │   ├── services/      # match, pull-consumer, analytics, host-session
│   │   ├── schemas/       # Pydantic request/response models
│   │   └── api/           # routers (host, player), deps, auth, websocket
│   ├── tests/
│   ├── pyproject.toml     # or requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── theme/
│   │   └── types/
│   ├── package.json
│   └── README.md
├── docker-compose.yml     # orchestrates backend + frontend (+ reverse proxy)
├── docker-compose.dev.yml # optional dev override (hot reload, bind mounts)
├── backend/Dockerfile
├── frontend/Dockerfile
├── .env.example           # documents every env var
├── README.md              # root: how to run both + the full host/player flow
└── prompt.md              # this file — leave as-is
```

---

## 3. Technology & Standards

**Backend**
- Python **3.11+**, **FastAPI**, **Uvicorn**.
- **Pydantic v2** for all schemas/settings (`pydantic-settings` for config).
- **SQLite** persistence **behind repository interfaces** (ABC/`Protocol`). Use the stdlib `sqlite3` or SQLModel/SQLAlchemy — your choice, but callers depend only on the repo interface, never on SQLite. Use a single connection with proper locking, or a connection-per-request pattern; SQLite must be opened with `check_same_thread=False` **only** if you serialize access (see §12 concurrency).
- Dependency injection via FastAPI `Depends` for repos, queue, services, settings.
- Tests with **pytest** (+ `httpx`/`TestClient`, and `pytest-asyncio` if needed).
- Lint/format: **ruff** + **black** (or ruff-format). Type-check friendly (mypy-clean ideally).

**Frontend**
- **React 18 + Vite + TypeScript**. Function components + hooks. Strict TS (`strict: true`).
- Routing: **react-router**. State: Context + hooks (no Redux). Data fetching: a thin typed `fetch` client (or TanStack Query if you prefer, but keep it light).
- Charts: **Recharts** (or clean custom SVG) for analytics.
- QR: **`qrcode.react`** (or equivalent) to render the join QR client-side.
- Pixel font: self-host an **open-licensed** pixel font (e.g. "Press Start 2P" — SIL OFL; bundle the font file, don't hotlink). Use `image-rendering: pixelated` and a consistent pixel grid.
- Lint/format: ESLint + Prettier.

**Engineering standards (throughout):** SOLID, clean code, small single-responsibility modules, meaningful names, no dead code, no giant files, full type coverage, and tests for core logic. Pure game rules must be framework/IO-free and independently unit-tested.

---

## 4. Configuration (single source of truth)

All tunables come from environment/settings with sane defaults. Provide `.env.example`. Suggested settings:

| Var | Default | Meaning |
|-----|---------|---------|
| `HOST_PASSWORD` | `Inter>Gremio` | Host login password (validated server-side). |
| `HOST_TOKEN_TTL_SECONDS` | `21600` | Host session token lifetime (6h). |
| `SECRET_KEY` | (random dev default; required in prod) | Signs host tokens. |
| `DATABASE_URL` | `sqlite:///./corda_brava.db` | SQLite location. |
| `CORS_ORIGINS` | `*` (dev) | Allowed frontend origins. |
| `TICK_INTERVAL_MS` | `500` | Consumer loop period (process queue + broadcast). |
| `DEFAULT_MATCH_DURATION_S` | `120` | Default match length. |
| `MATCH_DURATION_MIN_S` / `MAX_S` | `30` / `600` | Allowed configured durations. |
| `ROPE_TARGET` | `100` | Rope travel to each side to win (see §6). |
| `PULL_UNIT` | `1.0` | Rope units moved per single pull (before normalization). |
| `MAX_PULLS_PER_BATCH` | `200` | Anti-cheat clamp on a single batch count. |
| `BATCH_DEDUP_TTL_S` | `30` | Window to remember `batchId`s for idempotency. |
| `LATE_JOIN_POLICY` | `block` | `block` or `spectator` once match is running (see §9). |
| `TEAM_BALANCE_MODE` | `normalized` | `raw` or `normalized` scoring (see §6). |
| `QUEUE_BACKEND` | `memory` | `memory` or `azure_service_bus` — resolved by `make_event_queue()` factory. |
| `QUEUE_LEASE_TIMEOUT_S` | `10` | In-memory lease: unacked received messages become visible again after this. |
| `AZURE_SERVICEBUS_CONNECTION_STRING` | (unset) | Read only when `QUEUE_BACKEND=azure_service_bus`. |
| `AZURE_SERVICEBUS_QUEUE_NAME` | (unset) | Read only when `QUEUE_BACKEND=azure_service_bus`. |

Frontend reads its API/WS base URL from Vite env (`VITE_API_BASE`, `VITE_WS_BASE`), with a dev default. The join URL embedded in the QR must be reachable from phones on the LAN — document that the host should set the machine's LAN IP (e.g. `VITE_PUBLIC_BASE`) so QR links aren't `localhost`.

---

## 4b. Docker & Deployment (required — must run via Docker Compose)

The whole stack must come up with a single `docker compose up` and be deployable to a **VPS**. Design for both local dev and production.

**Images**
- `backend/Dockerfile`: multi-stage, slim Python base (e.g. `python:3.11-slim`), non-root user, install deps, run via **Uvicorn** (optionally behind Gunicorn with a Uvicorn worker — but note the consumer loop/WS implies you should run **a single worker/process** unless match state is externalized; document this constraint). Expose the API port. Add a `HEALTHCHECK` hitting a `/health` endpoint (add one).
- `frontend/Dockerfile`: multi-stage — build the Vite app (`npm ci && npm run build`), then serve the static bundle with **nginx** (slim). nginx must support SPA routing (fallback to `index.html`) and must **proxy `/api` and the WS upgrade** to the backend service (correct `Upgrade`/`Connection` headers for WebSocket). Alternatively use a dedicated reverse-proxy service (see below) — pick one approach and keep it clean.

**Compose topology**
- Services: `backend`, `frontend` (nginx serving the build), and **either** nginx-in-frontend doing the `/api`+WS proxy **or** a separate `proxy` (nginx/Traefik/Caddy) terminating one public port and routing `/` → frontend and `/api` + WS → backend. Prefer a **single exposed public port** (e.g. `80`, and `443` in prod) so phones hit one origin — this also sidesteps CORS and makes the QR URL clean.
- A named **volume** for the SQLite file so match data survives container restarts (even though it's a party game, don't lose state on a redeploy mid-event).
- `.env` wired into compose (`env_file`), driving `HOST_PASSWORD`, `SECRET_KEY`, `CORS_ORIGINS`, `VITE_PUBLIC_BASE`, etc. **`SECRET_KEY` and `HOST_PASSWORD` must be overridable at deploy time** and must not ship with insecure values baked into the image.
- `restart: unless-stopped` on long-lived services. Sensible `depends_on` + healthchecks so frontend/proxy wait for a healthy backend.
- `docker-compose.dev.yml` override: bind-mount source for hot reload (Uvicorn `--reload`, Vite dev server), expose ports directly, relaxed CORS. Base `docker-compose.yml` is production-shaped (built images, proxy, volume, restart policies).

**VPS notes (document in README):**
- Single public origin via the proxy; for the QR to work, `VITE_PUBLIC_BASE` must be the VPS's public hostname/IP (not `localhost`).
- WebSocket must pass through the proxy (document the upgrade headers).
- A short section on enabling TLS (e.g. Caddy auto-HTTPS or nginx + certbot) — implement Caddy auto-HTTPS if easy, otherwise document the manual step. `wss://` must work in prod so phones on mobile data can reach it.
- Because runtime match state lives in-process (consumer loops, WS sets, in-memory queue), the backend runs as **one instance**. Call this out as the current scaling limitation and tie it to the already-abstracted queue/repositories as the future path to horizontal scaling.

**Definition of done for this section:** `docker compose up` (prod file) brings up the full app reachable on one port; `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` gives a hot-reload dev environment; data persists across restarts via the volume; README documents local, dev, and VPS deployment.

---

## 5. Match State Machine

A `Match` moves through explicit states. Illegal transitions return `409 Conflict`.

```
LOBBY  ──start──▶  RUNNING  ──win/timeout──▶  FINISHED  ──reset──▶ (new match)
  │                                              ▲
  └───────────────── cancel (host) ─────────────┘
```

- **LOBBY:** players may join; host configures duration; host may start.
- **RUNNING:** pulls accepted; timer counts down (server-authoritative); rope updates each tick.
- **FINISHED:** carries `result` (`INTER` | `GREMIO` | `DRAW`), final scores, end reason (`win` | `timeout`), and frozen analytics inputs.

Guard every endpoint by state (e.g., pulls only in `RUNNING`, join only in `LOBBY` unless spectator policy).

---

## 6. Game Rules (the math — implement in `domain/`, unit-tested)

Define rope position as a single number `rope ∈ [-ROPE_TARGET, +ROPE_TARGET]`, starting at `0` (center). Positive = toward Grêmio's side, negative = toward Inter's side (or pick a convention and be consistent — expose it clearly to the frontend so it animates correctly).

Each consumer tick processes all pending pull events into **per-team pull totals for that tick**: `pulls_inter`, `pulls_gremio`.

**Scoring modes (`TEAM_BALANCE_MODE`):**
- **`raw`:** each pull contributes `PULL_UNIT`. Net rope delta this tick = `(pulls_gremio - pulls_inter) * PULL_UNIT`. Simple, but a team with more players dominates.
- **`normalized` (default, recommended):** to keep it fair regardless of team sizes, normalize each team's contribution by its active player count:
  `effort_team = (pulls_team / max(player_count_team, 1)) * PULL_UNIT`
  `rope_delta = (effort_gremio - effort_inter)`
  This rewards *per-player intensity*, so 2 fired-up players can beat 6 lazy ones. Document the chosen formula in the README and make it swappable.

Apply: `rope = clamp(rope + rope_delta, -ROPE_TARGET, +ROPE_TARGET)`.

**Win condition:** if `rope >= +ROPE_TARGET` → Grêmio wins; if `rope <= -ROPE_TARGET` → Inter wins; match ends immediately (`end reason = win`).

**Draw:** if the server timer hits `0` before either threshold → `DRAW` (`end reason = timeout`). (Optional tiebreak if you want: whoever is closer to winning takes it — but **default is a true draw**; keep it as a documented toggle if implemented.)

**Timer:** **server-authoritative.** On `start`, record `started_at` and `ends_at = started_at + duration`. Each tick computes remaining time from the clock; never trust client time for the timer. The host WS broadcasts remaining seconds; the host UI may smoothly interpolate between ticks for display only.

Keep `apply_pulls(tick_input) -> new_state`, `check_win(state)`, and `resolve_result(state)` as **pure functions** over the match/domain state.

---

## 7. Pull Submission Pipeline (core mechanic)

**Mobile client (dedicated `usePullBuffer` hook/module, unit-tested):**
- Local state: `displayCount` (what the player sees) and `pendingBatch` (pulls not yet acknowledged by the server).
- On each tap: `displayCount++`, `pendingBatch++`, fire the **"+1" juice** immediately. Tapping must never await the network.
- Every `FLUSH_INTERVAL_MS` (~500–1000ms) **and** on `visibilitychange`/`pagehide`: if `pendingBatch > 0`, send one `POST .../pulls` with `{ playerId, playerToken, count, clientTs, batchId }` where `batchId` is a fresh client UUID per batch.
- **Resilience:** snapshot the count being sent; only clear it on HTTP 2xx. On failure/timeout, **merge it back** so no pulls are lost. The server dedups by `batchId` so a retried batch isn't double-counted.
- Use `navigator.sendBeacon` for the final flush on `pagehide` when possible.
- Clamp client-side at `MAX_PULLS_PER_BATCH` too (defense in depth), but the server is the authority.

**Backend ingest endpoint:**
- Validate player belongs to match + match is `RUNNING`.
- Dedup: if `batchId` seen within `BATCH_DEDUP_TTL_S`, ack without re-enqueuing (idempotent).
- Clamp `count` to `MAX_PULLS_PER_BATCH`.
- **Enqueue** a `PullEvent` onto the `EventQueue` and return quickly (`202 Accepted`). The endpoint does no scoring itself.

**EventQueue abstraction (required — must swap to a cloud broker with ZERO consumer changes):**

A future requirement is to replace the in-memory queue with a managed cloud broker (e.g. **Azure Service Bus**, or SQS/RabbitMQ/Redis). The interface and the consumer **must be designed today around a broker-shaped contract** so that swap is *only* "add one adapter class + flip one env var" — no changes to the consumer, services, or domain. Do **not** design an in-memory-only interface (no synchronous "drain everything and it's gone" semantics that a network broker can't honor).

Design for these broker realities now:
- **Async, batched receive with a wait** (not instantaneous drain): `receive_batch(max_messages, max_wait)` may return fewer than `max`, or empty.
- **Explicit acknowledgement (at-least-once):** received messages are **leased**, not deleted. The consumer calls `ack()` **only after it has durably applied** them. On crash/no-ack, a broker redelivers → **the consumer must be idempotent** (reuse the existing `batchId` dedup — it is load-bearing here, not just anti-cheat). Optionally support `abandon()` / dead-letter.
- **Provider-agnostic envelope:** wrap payloads in a `QueueMessage` (fields: `id`, `payload: PullEvent`, `delivery_count`, `raw`/handle) so a vendor SDK's message type never leaks into services/domain.
- **Connection lifecycle & config:** backends open/close clients; selection is config-driven via a factory.

```python
# domain/queue-facing types are provider-agnostic
@dataclass
class QueueMessage:
    id: str                 # broker message id (or batchId for in-memory)
    payload: PullEvent
    delivery_count: int = 1

class EventQueue(Protocol):
    async def start(self) -> None: ...                 # connect (no-op in memory)
    async def close(self) -> None: ...
    async def enqueue(self, event: PullEvent) -> None: ...
    async def receive_batch(
        self, max_messages: int, max_wait_s: float
    ) -> list[QueueMessage]: ...                        # leased, not deleted
    async def ack(self, messages: list[QueueMessage]) -> None: ...   # complete/remove
    async def abandon(self, messages: list[QueueMessage]) -> None: ...  # optional: release lease
```

Ship an **in-memory** implementation today that honors this exact contract (async; `receive_batch` leases messages and only an `ack` truly removes them; unacked messages become visible again after a short lease timeout so redelivery/idempotency is genuinely exercised — add a simple test that kills a batch before ack and asserts redelivery). The Service Bus implementation later is a new file `AzureServiceBusEventQueue(EventQueue)` using `azure-servicebus` (async `ServiceBusClient`, `receive_messages`, `complete_message`) — **and nothing else in the codebase changes.**

Selection via config: `QUEUE_BACKEND=memory|azure_service_bus` (default `memory`) resolved by a `make_event_queue(settings)` factory wired through DI. Azure settings (`AZURE_SERVICEBUS_CONNECTION_STRING`, `AZURE_SERVICEBUS_QUEUE_NAME`) are read only when that backend is selected.

**Consumer loop (one per running match, single-writer):**
- Runs every `TICK_INTERVAL_MS` (~0.5s) as an asyncio background task started on match `start` and cancelled on `finish`/`reset`.
- Steps per tick: `msgs = await queue.receive_batch(max_messages, max_wait_s)` → **dedup by `batchId`** (idempotent; a redelivered batch is ignored) → aggregate per team → persist each new event for analytics → `apply_pulls` → `check_win` → update timer/remaining → **`await queue.ack(msgs)`** only after state is durably applied → if win/timeout set `FINISHED` + `result` and stop the loop → **broadcast** new state to the host WS.
- **Idempotency is mandatory:** because the broker contract is at-least-once, applying the same `batchId` twice must have no extra effect. Ack happens after apply, so a crash before ack causes safe redelivery, not lost pulls.
- This loop is the **single writer** of match runtime state → no races with the ingest endpoint (which only enqueues).
- The receive/ack shape is identical for in-memory and Azure Service Bus, so swapping backends needs **no changes here**.

Keep queue, consumer, scoring, analytics as **separate, testable units**.

---

## 8. Host Authentication (required)

- `POST /host/login { password }` → compare to `HOST_PASSWORD` using a **constant-time** comparison (`secrets.compare_digest`). On success return `{ token, expiresAt }`.
- Token = signed (e.g. **JWT** via `PyJWT`, or an itsdangerous signed token) carrying `role=host` + expiry, signed with `SECRET_KEY`. (Short-lived; no refresh needed for a party game.)
- Host HTTP endpoints require `Authorization: Bearer <token>` → a `require_host` dependency validates signature + expiry, else `401`.
- **Host WebSocket auth:** the browser WS API can't set headers, so accept the token as a **query param** `?token=...` (or via the first WS message / subprotocol). Validate on connect; if invalid, **accept-then-close with code 1008** (or refuse) — don't leave it open.
- Player endpoints are **public** (no host password). A player token (see §10) scopes a player to their own match/player id for pull submission.
- Enable CORS for the frontend origin(s). Never check the password only on the client.

---

## 9. Edge Cases & Policies (decide explicitly, document in README)

- **Late join (match already RUNNING):** default `LATE_JOIN_POLICY=block` → return `409` with PT-BR message ("A partida já começou"). If `spectator`, let them watch a read-only end-result-style screen. Pick `block` unless told otherwise.
- **Empty team at start:** warn on host start if a team has 0 players; allow start but the empty team simply can't pull (and normalized mode handles divide-by-zero via `max(count,1)`).
- **Player disconnect/reload mid-match:** player state is server-held; on reload the phone restores identity from the `localStorage` deviceId + player token and resumes on the correct screen (play or end) via `GET .../me`.
- **Host WS disconnect/reload mid-match:** the consumer loop keeps running server-side; the host reconnects to the WS and receives a full **state snapshot** on connect (not just deltas), so the scene resyncs.
- **Pull flood / scripted abuse:** per-batch clamp (`MAX_PULLS_PER_BATCH`) + `batchId` idempotency + match-state gating. Optionally a soft per-player rate sanity cap per tick. This is a party game, not a fortress — aim for "casual cheating is hard", documented honestly.
- **Multiple matches at once:** support more than one live match keyed by match id (registry of running consumer loops + per-match WS connection sets). At minimum, correctly isolate state per match id.
- **Reset:** host `reset`/new-match tears down the old consumer loop + closes its WS set and transitions cleanly.

---

## 10. One Player Per Device (required)

- On first visit the player client generates a **UUID in `localStorage`** (`useDeviceId` hook) and sends it on join.
- Join returns a **player token** (opaque or signed) the phone stores and sends with pulls and `GET /me`.
- Backend keys players by `(matchId, deviceId)` with a **unique constraint**. A second join from the same device **returns the existing player** (idempotent rejoin) rather than creating a duplicate; a *different* name/team from the same device returns the existing player (don't allow silent team-swapping mid-lobby unless you explicitly design a "change team" action).
- Tabs share `localStorage` → same device → same player. Document that this stops casual multi-join, not a determined attacker (incognito/another device bypasses it by design).

---

## 11. Data Model (SQLite behind repositories)

Entities (shape them as Pydantic domain models + SQLite tables; repositories translate):

**Match**
- `id` (short, URL-safe code, e.g. 6 chars), `status` (`LOBBY|RUNNING|FINISHED`), `created_at`
- `config`: `duration_s`, `rope_target`, `balance_mode`, team defs (`inter`, `gremio`: id/name/colors)
- runtime: `rope_position`, `started_at`, `ends_at`, `result` (`INTER|GREMIO|DRAW|null`), `end_reason` (`win|timeout|null`)

**Player**
- `id`, `match_id` (FK), `device_id`, `name`, `team` (`INTER|GREMIO`), `token`, `joined_at`
- unique `(match_id, device_id)`

**PullEvent** (one row per processed batch — enough to reconstruct all analytics)
- `id`, `match_id` (FK), `player_id` (FK), `team`, `count`, `client_ts`, `server_ts`, `batch_id`
- index on `(match_id, server_ts)` for time-bucketed analytics; unique `(match_id, batch_id)` for dedup

Repositories: `MatchRepository`, `PlayerRepository`, `EventRepository` — interfaces + SQLite impls. No SQLite types leak past the repo boundary.

---

## 12. Concurrency Model (be deliberate)

- FastAPI runs async; the **consumer loop is an `asyncio` task per running match**. It is the **only** writer of match runtime state.
- The ingest endpoint only **enqueues** (no state writes) → no lock contention with the loop.
- **SQLite** is single-writer: funnel all writes through the consumer loop / a single async-safe repository access pattern, or wrap writes in a lock. Prefer: loop owns runtime writes; join/login are infrequent and can take a short lock. Use WAL mode (`PRAGMA journal_mode=WAL`) to ease read concurrency.
- WS broadcast: maintain a per-match set of host connections; broadcasting iterates a snapshot of that set and drops dead sockets safely.
- On match end or reset: cancel the task, await its cleanup, close WS connections.

---

## 13. HTTP API (design fully; FastAPI `/docs` must work)

Prefix suggestion: `/api`. All request/response bodies are Pydantic models. User-facing errors carry PT-BR `detail`. Use correct status codes (`200/201/202/400/401/403/404/409/422`).

**Host (require `role=host` token):**
- `POST /host/login` → `{ token, expiresAt }`
- `POST /host/matches` `{ durationS?, balanceMode? }` → `{ matchId, joinUrl, qrPayload, config }`
- `GET  /host/matches/{id}` → full host view (state, config, roster, scores, rope, remaining)
- `PATCH /host/matches/{id}` `{ durationS }` (LOBBY only) → updated config
- `POST /host/matches/{id}/start` → transitions to RUNNING (spins up consumer loop)
- `POST /host/matches/{id}/reset` → tears down + returns to a fresh match (or creates new)
- `POST /host/matches/{id}/cancel` (optional) → FINISHED/cancelled
- `GET  /host/matches/{id}/analytics` → computed analytics payload (also pushable over WS at end)

**Player (public):**
- `GET  /matches/{id}/public` → `{ status, teams: {inter, gremio: {name, colors}}, counts }` to render join/wait
- `POST /matches/{id}/players` `{ name, team, deviceId }` → `{ playerId, playerToken, team }` (one-per-device)
- `POST /matches/{id}/pulls` `{ playerId, playerToken, count, clientTs, batchId }` → `202` (enqueue)
- `GET  /matches/{id}/me?playerId=&token=` → `{ screen: 'wait'|'play'|'end', team, matchStatus, result? }` (light polling to switch screens + show result; keep payload tiny)

Validate `team` against the match's team ids. Reject name that's empty/too long (trim, cap length, basic profanity screen optional). Rate-limit login attempts lightly.

---

## 14. Host WebSocket Contract

`WS /api/host/matches/{id}/ws?token=<hostToken>`

On connect: validate token → add to match's connection set → **immediately send a full `snapshot`**. Then push updates each tick / on roster change.

**Server → client messages** (discriminated by `type`):
```jsonc
// full state (on connect, and may be resent after reconnect)
{ "type": "snapshot", "match": {
    "id": "ABC123", "status": "LOBBY|RUNNING|FINISHED",
    "config": { "durationS": 120, "ropeTarget": 100, "balanceMode": "normalized",
                "teams": { "inter": {...}, "gremio": {...} } },
    "roster": { "inter": [ { "id","name" } ], "gremio": [ ... ] },
    "rope": 0, "remainingS": 120,
    "scores": { "inter": { "pulls": 0 }, "gremio": { "pulls": 0 } },
    "result": null, "endReason": null } }

// a player joined the lobby (drives the animated roster)
{ "type": "player_joined", "team": "INTER", "player": { "id","name" } }

// per-tick runtime update during RUNNING
{ "type": "tick", "rope": -12.5, "remainingS": 97,
  "delta": { "inter": 8, "gremio": 3 },          // pulls applied this tick
  "scores": { "inter": { "pulls": 140 }, "gremio": { "pulls": 95 } } }

// match ended
{ "type": "ended", "result": "INTER|GREMIO|DRAW", "endReason": "win|timeout",
  "finalRope": -100, "analytics": { /* see §15 */ } }
```

Keep messages small; `tick` carries only what the scene needs to animate. The frontend interpolates rope/timer visually between ticks. Define these as shared TS types mirrored from the Pydantic schemas.

---

## 15. Analytics (host end screen)

Computed from `PullEvent` rows (frozen at match end). Return via `GET .../analytics` and in the `ended` WS message. Render with charts + indicator tiles, pixel-art-styled.

**Overall:**
- `result`, `endReason`, `durationS` actually played.
- `totalPlayers`, `playersPerTeam`.
- `totalPulls` overall + per team.
- `pullsPerSecond` **timeline** (bucket events by ~1s → array of `{ t, inter, gremio }`) → line/area chart of intensity over the match.
- `peak`: the highest-intensity second (value + timestamp).
- Final rope position / how decisive the win was.

**Per-player / per-team:**
- `bestPlayer` and `worstPlayer` **of each team** (by total pulls).
- Per player: `pulls`, `% of own team total`, `% of all pulls`, pulls/sec average.
- `avgPullsPerPlayer` per team.
- A tasteful leaderboard (top N).

Put analytics computation in an `AnalyticsService` as pure-ish functions over events → unit-test the bucketing and the best/worst/percentage math.

**Players never see detailed analytics** — their end screen is just the result + "Obrigado por jogar!".

---

## 16. Frontend Screens & Structure

**Pages**
- Host: `HostLogin`, `HostCreate`, `HostLobby` (QR + animated roster), `HostMatch` (rope scene), `HostResults` (mascots + analytics + "Nova Partida").
- Player: `PlayerJoin` (name + team), `PlayerWait` ("aguardando o host iniciar"), `PlayerPlay` (PUXAR + +1 juice), `PlayerEnd` (result + thanks).

**Components:** `QRCode` (clickable → fullscreen overlay), `TeamColumn`, `PlayerIcon` (animates in), `RopeScene`, `Rope`, `Mascot` (states: `idle|straining|winning|losing|happy|crying`), `PullButton`, `Timer`, `ResultBanner`, `AnalyticsGrid`, chart wrappers.

**Hooks:** `useHostSocket(matchId, token)` (connect, snapshot, reconnect w/ backoff, typed messages), `usePullBuffer()` (count/flush/retry/batchId/flush-on-hide), `useDeviceId()`, `useCountdown()` (visual interpolation only).

**api/**: typed client (`hostApi`, `playerApi`) + `types/` mirrored from backend schemas.

**theme/**: single source for team tokens (colors, crest, mascot), pixel font, spacing, z-index for overlays, animation tokens.

**Pixel-art & motion:** `image-rendering: pixelated`, pixel grid, CSS transforms/keyframes; use `requestAnimationFrame` for smooth rope interpolation toward the latest `tick` target. Juice: button press, floating "+1", screen shake on big swings, particle bursts, optional sound hooks (structure them even if muted by default). Target 60fps; avoid layout thrash (animate transforms/opacity).

---

## 17. Responsiveness & Devices (required)

- **Player = mobile-first**, portrait-primary, correct across small→large phones; respect safe-area insets (notches/home bar); the **PUXAR** button is large and thumb-reachable on every size. No horizontal scroll, no clipped content.
- **Host = large displays** (laptop/projector/TV) first, degrading gracefully on smaller windows; QR overlay large and scannable; rope scene scales to viewport.
- Verify at multiple breakpoints.

---

## 18. Quality Bar — Definition of Done

- Full flow works end-to-end on a LAN: host login → create → QR → **real phones** join → start → spam PUXAR → rope moves live on host (via WS) → win or draw → player end screen + host analytics → new match.
- Host auth blocks unauthenticated access to **all** host HTTP endpoints **and** the host WS.
- One-player-per-device enforced; rejoin is idempotent; mid-match reloads resume correctly (player and host).
- Queue is a swappable abstraction (in-memory now); SQLite is behind repository abstractions; WAL + serialized writes; no runtime-state races (single-writer consumer loop).
- **Queue swap-readiness proven:** the `EventQueue` contract is broker-shaped (async, leased `receive_batch`, explicit `ack`, idempotent redelivery); the in-memory impl genuinely leases + redelivers unacked batches (with a test); the consumer applies-then-acks and is idempotent by `batchId`. README contains a **"Swapping to Azure Service Bus"** section listing the single file to add (`AzureServiceBusEventQueue`) + the env vars, and confirming no consumer/service/domain changes are required.
- Server-authoritative timer; normalized scoring keeps uneven teams fair.
- Pull pipeline loses no taps on flaky network; batches are idempotent; per-batch clamp applied.
- Analytics correct (unit-tested bucketing + best/worst/% math).
- Polished, cohesive, original pixel-art; **no copyrighted assets**; all player-facing text PT-BR.
- Backend domain logic unit-tested (lifecycle, scoring, win/draw, queue, consumer, analytics, dedup).
- `.env.example` documents every var; root `README.md` explains setup, LAN/QR note, and the host/player flow; design choices for any open detail are recorded.
- **`docker compose up` brings up the full stack on a single public port, deployable to a VPS; dev override gives hot reload; SQLite persists via a named volume; WS works through the proxy (incl. `wss://` guidance for prod).**

## 19. Suggested Build Order

1. Backend skeleton: settings, app factory, logging, domain entities + enums.
2. Pure game rules (`apply_pulls`, `check_win`, `resolve_result`) + **tests**.
3. Repo interfaces + SQLite impls (+ WAL, migrations/bootstrap) + **tests**.
4. `EventQueue` interface + in-memory impl + dedup + **tests**.
5. Host session/auth (login, token, `require_host`) + **tests**.
6. Services: match (lifecycle/state machine), pull-consumer loop, analytics (+ **tests**).
7. API routers (host + player) + host WebSocket; verify `/docs` + manual curl/ws.
8. Frontend skeleton: Vite+TS, routing, theme tokens, typed API client, `useDeviceId`.
9. Player flow: join → wait → play (`usePullBuffer`) → end.
10. Host flow: login → create → lobby (QR + animated roster via `useHostSocket`) → match scene (rope + mascots, interpolation) → results + analytics charts.
11. Pixel-art pass: mascots (incl. happy/crying states), crests, rope, animations, juice.
12. Responsive pass + end-to-end test on real phones; write READMEs + `.env.example`.
13. Dockerize: backend + frontend Dockerfiles, `docker-compose.yml` (prod: proxy, single port, volume, restart) + `docker-compose.dev.yml` (hot reload); add `/health`; verify full stack via `docker compose up` and document VPS deploy (TLS + `wss://`).

---

**Deliver a working, beautiful, clean implementation. Prefer clean architecture and a fun, polished experience wherever this spec leaves a choice open, and note such choices in the README.**
