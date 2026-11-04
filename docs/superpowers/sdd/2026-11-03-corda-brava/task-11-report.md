# Task 11 Report — Frontend skeleton

**Status:** DONE. **Commit:** `c1ecbdf` feat(frontend): skeleton — vite/ts, routing, theme, typed client, useDeviceId
**Results:** vitest 3/3 pass; `tsc --noEmit` clean; `npm run build` ok; `npm run lint` clean.

## Files (frontend/)
package.json, package-lock.json, tsconfig.json (strict), vite.config.ts, vitest.config.ts, eslint.config.js, index.html,
src/{main.tsx, App.tsx, vite-env.d.ts}, src/theme/{tokens.ts, global.css}, src/types/api.ts,
src/api/{client.ts, hostApi.ts, playerApi.ts}, src/hooks/{useDeviceId.ts, useDeviceId.test.ts},
src/assets/fonts/{PressStart2P.woff2, OFL-LICENSE.txt} (from @fontsource/press-start-2p, latin 400).

## Scripts
dev (vite), build (`tsc --noEmit && vite build`), preview, test (vitest), lint (`eslint src`).
Dev proxy: `/api` (ws on) -> http://localhost:8000; dev server binds all interfaces.

## Env vars (all optional)
- VITE_API_BASE default "" (same-origin relative paths)
- VITE_WS_BASE default "" (derived from page origin, http->ws / https->wss)
- VITE_PUBLIC_BASE default window origin; exported as `PUBLIC_BASE` (set to LAN IP/host for QR)

## Types (src/types/api.ts) — mirror backend JSON
TeamId ("inter"|"gremio"), TeamUpper, MatchStatus (LOBBY|RUNNING|FINISHED), MatchResult (INTER|GREMIO|DRAW), EndReason (win|timeout), BalanceMode,
TeamColors, TeamConfig, ConfigOut, RosterPlayer, TeamScore, MatchView, PlayerStats, TeamStats, AnalyticsPayload,
WS: Snapshot, PlayerJoinedMsg (team UPPERCASE), TickMsg, EndedMsg, CancelledMsg, ResetMsg, HostWsMsg (union on `type`),
HTTP: LoginResponse, CreateMatchRequest, CreateMatchResponse, PublicMatch, JoinRequest, JoinResponse, PullRequest, PullAccepted, MeResponse.
Player-side `team` (join, me, analytics) is lowercase; `result` always uppercase.

## API (src/api)
client.ts: `ApiError{status,message=PT-BR detail}`, `request<T>(path,{method?,body?,token?,query?})`, `wsUrl(path,query?)`, API_BASE, WS_BASE, PUBLIC_BASE.
hostApi.ts (token = Bearer): login(password), createMatch(token, body?), getMatch(token,id), patchMatch(token,id,durationS) -> ConfigOut,
startMatch(token,id), resetMatch(token,id) -> CreateMatchResponse of NEW match, cancelMatch(token,id), getAnalytics(token,id), hostWsUrl(id,token).
playerApi.ts: getPublic(id), join(id,JoinRequest), sendPulls(id,PullRequest), getMe(id,playerId,token).
hooks: `getDeviceId()` (plain fn, key `cb.deviceId`, localStorage in try/catch, crypto.randomUUID with fallback), `useDeviceId()`.

## Theme tokens
tokens.ts: `teams` {inter:{primary #E5050F,secondary #FFFFFF,dark #7A0309}, gremio:{primary #0D80BF,secondary #000000,light #4FA9DC}}, `colors` (bg,panel,text,muted),
`spacing` (xs4 sm8 md16 lg24 xl40), `zIndex` (base,scene,hud,overlay,toast), `fonts.pixel`, `motion`.
global.css vars: --inter --inter-dark --gremio --gremio-light --gremio-black --bg --panel --text --muted --sp-{xs,sm,md,lg,xl} --z-{scene,hud,overlay,toast} --font-pixel --safe-top --safe-bottom; @font-face "Press Start 2P".

## Routes (App.tsx, placeholders)
/ -> redirect /host/login; /host/login; /host/create; /host/lobby/:id; /host/match/:id; /host/results/:id; /j/:id (join); /j/:id/wait; /j/:id/play; /j/:id/end; * -> /.

## Deviations
- ESLint flat config (eslint.config.js) instead of .eslintrc (ESLint 10). No Prettier added.
- Font woff2 copied into src/assets/fonts (not imported from npm package).
- Added vitest.config.ts (jsdom) separate from vite.config.ts; test exports `getDeviceId` for non-React testing.
- Placeholder pages live in App.tsx as one small component; no per-page files yet. No mascot/crest code added.
