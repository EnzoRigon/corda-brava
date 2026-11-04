### Task 10: Host API routes + host WebSocket (snapshot + tick broadcast)

**Files:**
- Create: `backend/app/api/host.py`, `backend/app/api/ws.py`, `backend/app/schemas/match.py`
- Test: `backend/tests/api/test_host_routes.py`, `backend/tests/api/test_host_ws.py`

**Interfaces:**
- Consumes: MatchService, analytics, auth (`require_host`, `verify_ws_token`), registry.
- Produces: `POST /api/host/login`; `POST /api/host/matches`→`{matchId,joinUrl,qrPayload,config}`; `GET /api/host/matches/{id}`; `PATCH /api/host/matches/{id}`; `POST .../start|reset|cancel`; `GET .../analytics`. `WS /api/host/matches/{id}/ws?token=` → validate (bad→accept+close 1008), register in match set, **send full `snapshot` immediately**, then push `player_joined`/`tick`/`ended` messages per `prompt.md §14`. Broadcast iterates a snapshot of the set, drops dead sockets. Consumer's broadcast callback (Task 6) wired to this set.

- [ ] **Step 1:** Write tests: unauth host route → 401; login→token→create match 201; start transitions RUNNING; patch duration in RUNNING → 409; WS without token → closed 1008; WS with token → first message is `type:"snapshot"` with match/roster/rope/remaining; joining a player then reading WS yields `player_joined`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement routes + WS; wire broadcast callback into registry on start; tear down on reset/cancel.
- [ ] **Step 4:** Run → PASS; manually confirm `/docs` renders.
- [ ] **Step 5:** Commit `feat(api): host routes + host WebSocket (snapshot/tick/ended) + tests`.

---

