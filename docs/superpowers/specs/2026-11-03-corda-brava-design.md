# Corda Brava — Design Document

> Date: 2026-11-03. This document records the decisions layered on top of the
> execution-ready spec in `prompt.md`. It does **not** restate the whole spec —
> `prompt.md` is the authoritative requirements document. This captures the open
> choices the spec delegated, the owner-provided decisions, and the build/validation
> orchestration model.

## Intent & Why

A themed, mobile-join party game of tug-of-war (cabo de guerra) between **Inter**
(red) and **Grêmio** (blue/black). A host opens a big screen, players scan a QR
code on their phones, pick a team, and spam a "PUXAR" button. The rope moves live
on the host screen with two pixel-art mascots straining; first team to drag it to
their side wins, timeout is a draw, and the host sees celebration + analytics. Built
as a clean, well-architected reference implementation and a fun, polished experience.

Full behavioral/technical requirements: see `prompt.md` (sections 0–19). The
Definition of Done in §18 and build order in §19 are binding.

## Goals
- Full end-to-end flow working on a LAN and via `docker compose up` on one port.
- Clean architecture: pure domain rules (framework/IO-free, unit-tested),
  repository-abstracted SQLite, broker-shaped swappable `EventQueue`,
  single-writer consumer loop, server-authoritative timer.
- Faithful, instantly-recognizable mascots and crests; cohesive retro-arcade look.
- All player-facing copy in **PT-BR**; code/identifiers/comments in English.

## Non-goals / Anti-goals
- Not a commercial product; no official/copyrighted image files pulled from the web.
- Not horizontally scaled — backend runs as a single instance (documented limitation).
- No Redux, no heavyweight state libs on the frontend.
- A build that passes unit tests but the real host↔phone flow is broken = failure.

## Decisions on open choices (owner-confirmed 2026-11-03)

1. **Game name:** `Corda Brava` (spec default). Used consistently in UI, titles, README.

2. **Mascot art — USE PROVIDED SPRITES (overrides the spec's "author by code" default).**
   The project owner has already authored original pixel-art mascot sprites for this
   project and committed them at
   `docs/mascot-references/mascot-test/assets/`:
   - Inter "Saci": `saci_master.png`, `saci_pull.gif`, `saci_happy.gif`,
     `saci_cry.gif`, `saci_defeat.gif`
   - Grêmio "Mosqueteiro": `mosq_master.png`, `mosq_pull.gif`, `mosq_happy.gif`,
     `mosq_cry.gif`, `mosq_defeat.gif`
   These are self-contained, committed, original pixel-art renditions. The build
   **copies them into `frontend/src/assets/mascots/`** and the `Mascot` component
   selects the correct sprite per animation state. State→sprite mapping:
   - `idle` → `*_master.png` (static master pose)
   - `straining` → `*_pull.gif`
   - `winning`/`happy` → `*_happy.gif`
   - `losing` → `*_defeat.gif` (dragged/struggling)
   - `crying` → `*_cry.gif`
   - draw → both show `*_defeat.gif` (exhausted standoff) or master; pick master.
   The reference prototype at `docs/mascot-references/mascot-test/index.html` shows
   the intended rope-scene layout (fighters anchored to a rope line, knot slides).

3. **Team crests:** copy the owner-committed pixel-art crests
   `docs/logo-references/inter.png` and `docs/logo-references/gremio.png` into
   `frontend/src/assets/crests/`. Used in team columns, badges, result banners.
   These too are owner-authored committed files, used as-is (not re-rendered in code).

4. **Rope convention:** `rope ∈ [-ROPE_TARGET, +ROPE_TARGET]`, `0` = center.
   Negative → Inter side (left), Positive → Grêmio side (right). `rope <= -target`
   → Inter wins; `rope >= +target` → Grêmio wins. Frontend animates knot:
   `left% = 50 + (rope / ROPE_TARGET) * 40` (clamped 10–90%), matching the prototype.

5. **Scoring:** `TEAM_BALANCE_MODE=normalized` default (per-player intensity, fair for
   uneven teams). `raw` available via env. Formulas exactly per `prompt.md §6`.

6. **Draw:** true draw on timeout (no tiebreak). Documented toggle not implemented
   unless trivial.

7. **Late join:** `LATE_JOIN_POLICY=block` (409 "A partida já começou").

8. **Queue:** in-memory broker-shaped impl now, honoring the exact async/leased/ack
   contract in `prompt.md §7`, with a redelivery test. Azure Service Bus is a future
   single-file adapter; README documents the swap.

9. **Proxy topology (Docker):** single public port via a `proxy` service (nginx)
   routing `/` → frontend static bundle and `/api` + WS upgrade → backend. Named
   volume for SQLite. `docker-compose.dev.yml` override for hot reload. TLS guidance
   documented; implement Caddy auto-HTTPS only if it stays simple, else document nginx+certbot.
   (Builder may instead fold the proxy into the frontend nginx if cleaner — one approach,
   kept clean, single exposed port, documented.)

## Tech stack (per spec, non-negotiable)
- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2 + pydantic-settings, SQLite
  behind repo interfaces, pytest, ruff+black.
- Frontend: React 18 + Vite + TS (strict), react-router, Context+hooks, Recharts,
  `qrcode.react`, self-hosted "Press Start 2P" (OFL) font bundled (no hotlink),
  ESLint+Prettier.

## Build & validation orchestration (owner directive)
- **All implementation and validation is performed by dispatched subagents**
  (claude haiku/sonnet), never inline by the orchestrator. Parallel where tasks are
  independent; sequential where there are dependencies.
- **Validation uses the `/loop` pattern** so repeated test/fix cycles are cheap.
- **Validation scope = FULL:** backend pytest, frontend typecheck/lint/build,
  `docker compose up` smoke, and a Playwright-driven host+player end-to-end flow
  (login → create → QR/join → start → pull → result → analytics). The spec's DoD
  "works end-to-end" must be actually demonstrated, not assumed.

## What's left to the builder
- Exact pixel sizing/CSS of the rope scene beyond matching the prototype layout.
- Analytics chart styling specifics (within the retro-arcade theme).
- Minor API field shapes not pinned by §13/§14 (keep PT-BR error `detail`).
- Whether proxy is separate service vs folded into frontend nginx (keep it clean,
  single port, documented).
- Choice of JWT lib (PyJWT) vs itsdangerous for host token — PyJWT default.
