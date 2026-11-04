### Task 14: Player flow pages — Join → Wait → Play → End

**Files:**
- Create: `frontend/src/pages/PlayerJoin.tsx`, `PlayerWait.tsx`, `PlayerPlay.tsx`, `PlayerEnd.tsx`, `frontend/src/components/PullButton.tsx`, `frontend/src/hooks/useMePolling.ts`
- Test: `frontend/src/pages/PlayerJoin.test.tsx`

**Interfaces:**
- Consumes: playerApi, useDeviceId, usePullBuffer, `/me` polling.
- Produces: Join (name + team pick, PT-BR, calls join, stores playerToken) → Wait ("Aguardando o host iniciar") → Play (big thumb-reachable PUXAR + "+1" juice, displayCount) → End (result + "Obrigado por jogar!", **no analytics**). `useMePolling` switches screen on `/me` status; mid-match reload restores correct screen from stored token.

- [ ] **Step 1:** Write `PlayerJoin.test.tsx`: renders team options + name input in PT-BR; submitting calls join API with deviceId and navigates to wait.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement pages + PullButton + polling.
- [ ] **Step 4:** Run → PASS; `tsc` clean.
- [ ] **Step 5:** Commit `feat(frontend): player flow (join/wait/play/end) + PullButton + /me polling`.

