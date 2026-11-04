# Corda Brava — frontend

React 18 + Vite + TypeScript. Host screens (login, create, lobby, match, results) and player screens (join, wait,
play, end). Player-facing copy is PT-BR.

## Run

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api (incl. WebSocket) to http://localhost:8000
```

## Test, lint, build

```bash
npm test -- --run          # unit tests (vitest; e2e/ is excluded)
npm run lint && npx tsc --noEmit
npm run build
```

## End-to-end (Playwright)

The stack must already be running (backend on :8000 + `npm run dev`, or the Docker stack). Once per machine:
`npx playwright install chromium`.

```bash
npm run e2e                                   # against http://localhost:5173
E2E_BASE_URL=http://localhost npm run e2e     # against the Docker stack
E2E_HOST_PASSWORD=... npm run e2e             # if HOST_PASSWORD is not the default
```

`e2e/flow.spec.ts` drives a host and a player in separate browser contexts: login, create (30 s), join, start,
tap PUXAR, knot moves, match ends, end screen and results/analytics. It creates its own match.

## Env (build-time)

`VITE_*` variables are baked in at build time (Docker build args), not read at runtime:
`VITE_PUBLIC_BASE` (join-URL fallback), `VITE_API_BASE` / `VITE_WS_BASE` (leave empty for same-origin),
`VITE_PROXY_TARGET` (dev-server proxy target).

## Layout

```
src/api/         typed REST client
src/hooks/       useDeviceId, usePullBuffer, useHostSocket, useMePolling
src/pages/       Host* and Player* screens
src/components/  Mascot, Crest, RopeScene, PullButton, charts...
src/theme/       CSS + pixel font
e2e/             Playwright spec
```
