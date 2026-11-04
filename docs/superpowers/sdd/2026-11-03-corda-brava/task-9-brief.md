### Task 9: Player API — pulls ingest (enqueue/dedup/clamp) + `/me`

**Files:**
- Modify: `backend/app/api/player.py`
- Create: `backend/app/schemas/pulls.py`
- Test: `backend/tests/api/test_pulls_and_me.py`

**Interfaces:**
- Consumes: queue, repos, player-token verify.
- Produces: `POST /api/matches/{id}/pulls {playerId,playerToken,count,clientTs,batchId}` → **202** (validates player∈match, match RUNNING, dedup by batchId within `BATCH_DEDUP_TTL_S` → ack without re-enqueue, clamp to `MAX_PULLS_PER_BATCH`, else enqueue PullEvent). `GET /api/matches/{id}/me?playerId=&token=` → `{screen:'wait'|'play'|'end', team, matchStatus, result?}`.

- [ ] **Step 1:** Write tests: pull in RUNNING → 202 and queue has 1 msg; **same batchId again → 202 but queue not re-enqueued** (idempotent ingest); count clamped to MAX; pull when not RUNNING → 409; bad token → 401/403; `/me` returns `wait` in LOBBY, `play` in RUNNING, `end` + result in FINISHED.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(api): pull ingest (enqueue/dedup/clamp, 202) + /me + tests`.

