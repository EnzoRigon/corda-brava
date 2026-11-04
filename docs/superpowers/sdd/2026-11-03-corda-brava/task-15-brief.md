### Task 15: `useHostSocket` + Host Login/Create/Lobby pages (QR + animated roster)

**Files:**
- Create: `frontend/src/hooks/useHostSocket.ts`, `frontend/src/pages/HostLogin.tsx`, `HostCreate.tsx`, `HostLobby.tsx`, `frontend/src/components/QRCode.tsx`, `TeamColumn.tsx`, `PlayerIcon.tsx`
- Test: `frontend/src/hooks/useHostSocket.test.ts`

**Interfaces:**
- Consumes: hostApi, WS.
- Produces: `useHostSocket(matchId, token) -> {status, snapshot, lastTick, ended, connected}` — connects `?token=`, stores snapshot, applies `player_joined`/`tick`/`ended`, reconnects with backoff, typed messages. HostLogin (password → token in storage), HostCreate (duration/balance → create → navigate lobby), HostLobby (big clickable `QRCode` → fullscreen overlay of `joinUrl` from `VITE_PUBLIC_BASE`, animated roster via TeamColumn/PlayerIcon from snapshot/`player_joined`, Start button).

- [ ] **Step 1:** Write `useHostSocket.test.ts` (mock WebSocket): on open consumes a `snapshot` message and exposes it; a `player_joined` appends to roster; reconnect scheduled on close.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement hook + pages + components.
- [ ] **Step 4:** Run → PASS; `tsc` clean.
- [ ] **Step 5:** Commit `feat(frontend): useHostSocket + host login/create/lobby (QR + animated roster)`.

