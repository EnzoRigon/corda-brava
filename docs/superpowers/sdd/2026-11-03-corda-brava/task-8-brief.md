### Task 8: Player API — public info + join (one-per-device, idempotent)

**Files:**
- Create: `backend/app/api/player.py`, `backend/app/schemas/player.py`; wire `make_event_queue`, repos, services via `Depends` in `backend/app/api/deps.py`
- Test: `backend/tests/api/test_player_join.py`

**Interfaces:**
- Consumes: MatchService, repos, auth (player token issuance — opaque or signed with device+match+player).
- Produces: `GET /api/matches/{id}/public`; `POST /api/matches/{id}/players {name,team,deviceId}` → `{playerId,playerToken,team}`; player-token issue/verify helper. Join validates team against match teams, trims/caps name, **LATE_JOIN block → 409 PT-BR** when not LOBBY. Second join same device → existing player (idempotent, no dup).

- [ ] **Step 1:** Write tests (TestClient): create match (via service directly or host route), join returns player+token; **re-join same deviceId returns same playerId** (no new row); join with invalid team → 422/400; join when RUNNING + block policy → 409 with PT-BR detail "A partida já começou"; public endpoint shows counts.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement deps wiring + player router.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): player public + join (one-per-device idempotent) + tests`.

