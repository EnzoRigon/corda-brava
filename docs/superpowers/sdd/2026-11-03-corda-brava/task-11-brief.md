### Task 11: Frontend skeleton — Vite+TS, routing, theme tokens, typed API client, shared types

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json` (strict), `frontend/vite.config.ts`, `frontend/index.html`, `frontend/.eslintrc`, `frontend/src/main.tsx`, `frontend/src/App.tsx` (router), `frontend/src/theme/tokens.ts`, `frontend/src/theme/global.css`, `frontend/src/types/api.ts` (mirror Pydantic), `frontend/src/api/client.ts`, `frontend/src/api/hostApi.ts`, `frontend/src/api/playerApi.ts`, `frontend/src/hooks/useDeviceId.ts`
- Bundle: Press Start 2P font file under `frontend/src/assets/fonts/` + `@font-face`.
- Test: `frontend/src/hooks/useDeviceId.test.ts` (vitest)

**Interfaces:**
- Produces: theme tokens (Inter/Grêmio colors per design, spacing, z-index, pixel font); TS types mirroring §13/§14 messages (`Snapshot`, `TickMsg`, `EndedMsg`, `AnalyticsPayload`, etc.); typed `fetch` client reading `VITE_API_BASE`/`VITE_WS_BASE`/`VITE_PUBLIC_BASE`; `useDeviceId()` (localStorage UUID). Routes: `/host/login|create|lobby/:id|match/:id|results/:id`, `/j/:id` (player join), player wait/play/end.

- [ ] **Step 1:** Write `useDeviceId.test.ts`: returns a stable UUID persisted in localStorage across calls.
- [ ] **Step 2:** Run `npm test` → FAIL.
- [ ] **Step 3:** Scaffold app, routing, theme, types, client, font, `useDeviceId`.
- [ ] **Step 4:** Run → PASS; `npm run build` + `tsc --noEmit` clean.
- [ ] **Step 5:** Commit `feat(frontend): skeleton — vite/ts, routing, theme, typed client, useDeviceId`.

