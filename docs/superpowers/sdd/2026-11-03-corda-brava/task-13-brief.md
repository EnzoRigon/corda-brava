### Task 13: `usePullBuffer` hook (count/flush/retry/batchId/flush-on-hide)

**Files:**
- Create: `frontend/src/hooks/usePullBuffer.ts`
- Test: `frontend/src/hooks/usePullBuffer.test.ts`

**Interfaces:**
- Consumes: playerApi pull POST.
- Produces: `usePullBuffer({matchId,playerId,playerToken,flushIntervalMs}) -> {displayCount, tap()}`. `tap()`: `displayCount++`, `pendingBatch++`, never awaits. Flushes every interval + on `visibilitychange`/`pagehide` (sendBeacon when possible) with fresh `batchId` UUID per batch; snapshot count, clear only on 2xx, **merge back on failure** (no lost pulls). Clamp to `MAX_PULLS_PER_BATCH`.

- [ ] **Step 1:** Write tests (vitest + fake timers, mocked fetch): N taps → displayCount N instantly; after interval one POST with count=N and a batchId; POST rejects → next flush includes the merged-back count (nothing lost); 2xx clears pending.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(frontend): usePullBuffer (batch/retry/merge-back/flush-on-hide) + tests`.

