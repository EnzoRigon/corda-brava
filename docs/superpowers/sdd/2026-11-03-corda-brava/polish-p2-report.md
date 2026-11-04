# Polish P2 report

Commit: 1f386fb

Tick payload gained `events`: `[{playerId, name, team, count}]` (team lowercase, camelCase keys), one per pull batch applied that tick (deduped/dropped excluded), names from the already-loaded roster (no extra query). Capped to the most recent 20 (`new_events[-20:]`); empty tick sends `[]`.

Frontend: `TickEvent` + `TickMsg.events` in frontend/src/types/api.ts (tsc clean, reducer needed no change).

Tests: names/teams/counts for 2 players, duplicate redelivery absent, cap of 20 (25 batches), WS key-set test updated.

Checks: pytest 146 passed, ruff, black, tsc, vitest clean. No deviations.
