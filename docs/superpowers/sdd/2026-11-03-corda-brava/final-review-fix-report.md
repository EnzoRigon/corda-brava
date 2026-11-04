# Final review fix report

| # | Item | Status | Test |
|---|------|--------|------|
| 1 | LAN-safe batch id (`newId` exported from `useDeviceId.ts`, used by `usePullBuffer`; no other `randomUUID` use) | fixed | `usePullBuffer.test.ts` "still posts with a batchId when crypto.randomUUID is missing" |
| 2 | Restart recovery: `MatchRepository.list_running`, `MatchService.resume_running` called from lifespan; expired matches finish on the loop's first tick (existing timeout logic); score totals restored by `ConsumerLoop.__init__` | fixed | `test_match_service.py::test_resume_running_restarts_loop_and_finishes_expired`, `test_host_routes.py::test_restart_recovers_running_match` |
| 3 | nginx `X-Forwarded-For $remote_addr`; `login_failures` pruned on each attempt | fixed | `test_host_routes.py::test_login_failures_pruned_...` (nginx.conf itself not testable) |
| 4 | Per-player per-tick cap, `MAX_PULLS_PER_PLAYER_PER_S=15` (settings + `.env.example`), excess dropped | fixed | `test_consumer.py::test_per_player_cap_limits_one_tick` |
| 5 | `registry.broadcast` 1.0s `wait_for` per listener, drop on timeout/error | fixed | `test_registry_broadcast.py` |
| 6 | PT-BR ConflictError messages in `match_service.py` (other details already PT-BR) | fixed | `test_match_service.py::test_ptbr_conflict_messages` |
| 7 | Cancel on FINISHED match returns 409 | fixed | `test_host_routes.py::test_cancel_finished_match_409` |
| 8 | "Partida cancelada" in ResultBanner and PlayerEnd for null result | fixed | `ResultBanner.test.tsx`, `PlayerEnd.test.tsx` |
| 9 | README counts + §1 deviation note; CLAUDE.md art-policy scope | fixed | n/a |

Existing test fixtures with 1-20 ms ticks got a high `MAX_PULLS_PER_PLAYER_PER_S` so the cap does not interfere.
Skipped: nothing (no forbidden files were needed).
