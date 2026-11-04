# Task 7 Report — Analytics service

**Date:** 2026-11-04
**Status:** DONE

## 1. Files

| File | Purpose |
|------|---------|
| `backend/app/schemas/analytics.py` | Pydantic `AnalyticsPayload` + nested models (camelCase fields, `# ruff: noqa: N815`) |
| `backend/app/services/analytics.py` | `compute_analytics` (pure, no IO) |
| `backend/tests/services/test_analytics.py` | 4 tests |

## 2. Public signature

```python
LEADERBOARD_SIZE = 5
def compute_analytics(match: Match, players: Sequence[Player],
                      events: Sequence[PullEvent], top_n: int = LEADERBOARD_SIZE) -> AnalyticsPayload
```
Serialize with `payload.model_dump(mode="json")`.

## 3. Payload JSON shape

```jsonc
{
  "result": "inter|gremio|draw|null", "endReason": "win|timeout|null",
  "durationS": 10, "totalPlayers": 4,
  "playersPerTeam": {"inter": 3, "gremio": 1},
  "totalPulls": {"overall": 20, "inter": 8, "gremio": 12},
  "pullsPerSecond": [{"t": 0, "inter": 5, "gremio": 0}],   // dense, t = 0..durationS-1
  "peak": {"value": 10, "t": 3},                           // earliest second wins ties; {0,0} if empty
  "finalRope": -30.0,
  "teams": {"inter": TeamStats, "gremio": TeamStats},
  "players": [PlayerStats],                                // all players, sorted
  "leaderboard": [PlayerStats]                             // top N of players
}
// TeamStats: {players, totalPulls, avgPullsPerPlayer, bestPlayer: PlayerStats|null, worstPlayer: PlayerStats|null}
// PlayerStats: {playerId, name, team, pulls, pctOfTeam, pctOfAll, pullsPerSec}  (pct 0-100, 2 dp)
```

## 4. Rules pinned
- Bucket = floor(server_ts - match.started_at) in seconds (clamped at 0); `PullEvent.count` is summed (batch aggregates).
- durationS: `config.duration_s` on timeout; on win, last pull second + 1 (capped at config). Timeline length = max(durationS, last bucket + 1).
- Ordering/ties: pulls desc, then name, then playerId (best = first, worst = last by the reversed key). Zero-pull players are included. Empty team: best/worst null, avg 0.0. All divisions guarded (0).
- Players with events but not in `players` are counted in totals only.

## 5. Results
- Tests: 95 passed (91 + 4 new). ruff and black clean.
- Commit: a56f7fb (code + task-7 brief).

## 6. Deviations
- Match has no `finished_at`, so "duration actually played" is derived as above (flag for Task 10 if a real finish timestamp is added).
- Leaderboard size is a module constant/param, not a setting (none existed).
- `totalPulls` is an object `{overall, inter, gremio}`, per-team stats live under `teams`.
