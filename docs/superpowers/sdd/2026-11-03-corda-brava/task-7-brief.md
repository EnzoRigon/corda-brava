### Task 7: Analytics service

**Files:**
- Create: `backend/app/services/analytics.py`, `backend/app/schemas/analytics.py`
- Test: `backend/tests/services/test_analytics.py`

**Interfaces:**
- Consumes: `PullEvent` list, players, match.
- Produces: `compute_analytics(match, players, events) -> AnalyticsPayload` with everything in `prompt.md §15`: result/endReason/durationS, totalPlayers, playersPerTeam, totalPulls overall+per team, `pullsPerSecond` timeline `[{t,inter,gremio}]` (1s buckets), `peak{value,t}`, finalRope; per-team best/worst player, per-player `{pulls, pctOfTeam, pctOfAll, pullsPerSec}`, `avgPullsPerPlayer`, leaderboard top N. Pure-ish functions.

- [ ] **Step 1:** Write tests pinning: 1s bucketing from `server_ts`; best/worst by total pulls per team; percentage math (`pct_of_team`, `pct_of_all`); peak second; empty events → zeros not crash.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(analytics): analytics service + bucketing/best-worst/% tests`.

