### Task 18: READMEs + end-to-end Playwright flow + full validation loop

**Files:**
- Create: `README.md` (root), `backend/README.md`, `frontend/README.md`, `frontend/e2e/flow.spec.ts` (Playwright), `frontend/playwright.config.ts`
- Test: the Playwright E2E itself is the test.

**Interfaces:**
- Consumes: the whole running stack.
- Produces: root README (setup local/dev/VPS, LAN/QR note with `VITE_PUBLIC_BASE`, host/player flow, recorded design choices, **"Swapping to Azure Service Bus"** section naming the single file `AzureServiceBusEventQueue` + env vars + "no consumer/service/domain changes", scaling limitation). Playwright E2E: host login → create → read joinUrl → open second context as player → join team → host start → player taps PUXAR repeatedly → host WS rope moves → match ends → player end screen + host analytics visible.

- [ ] **Step 1:** Write the Playwright spec driving two browser contexts (host + player) against the compose stack (or vite+uvicorn dev).
- [ ] **Step 2:** Run E2E → iterate until green.
- [ ] **Step 3:** Write the three READMEs incl. the Azure swap section and VPS/TLS/`wss://` guidance.
- [ ] **Step 4:** Full validation loop (see below) all green.
- [ ] **Step 5:** Commit `feat: READMEs + Playwright end-to-end flow; docs for Azure swap, VPS/TLS`.

---

## Full validation loop (run after each phase and at the end)

1. `cd backend && ruff check . && black --check . && pytest -q` → all pass.
2. `cd frontend && npm run lint && tsc --noEmit && npm test && npm run build` → all pass.
3. `docker compose config` valid; `docker compose up -d --build`; `/health` + `/` 200; `docker compose down`.
4. Playwright E2E green against the running stack.

If any step fails, fix within the owning task and re-run that step.
