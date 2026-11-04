# Task 16 Report — Host Match scene + Results + analytics charts

**Status:** DONE. Code commit: `6e82ccb`

## Files
- New: `pages/HostMatch.tsx`, `pages/HostResults.tsx`, `components/{RopeScene,Rope,Timer,ResultBanner,AnalyticsGrid}.tsx`, `components/charts/PullsTimeline.tsx`, `hooks/useCountdown.ts`
- Tests: `RopeScene.test.tsx`, `HostResults.test.tsx`, `useCountdown.test.tsx`
- Edited: `App.tsx` (routes, placeholder removed), `theme/global.css`, `package.json`/lock (`recharts`)

## Knot / interpolation
`knotLeftPercent(rope, target) = 50 + rope/target*40` (-target 10%, 0 50%, +target 90%); target = `snapshot.config.ropeTarget`. RopeScene eases toward it by 15%/frame with requestAnimationFrame (cancelled on unmount); `interpolate=false` snaps (used by tests). Shake class when the knot is >4 percentage points from its goal (big swing). Straining mascots scale up to 1.25 with `delta`.

## Mascot state per scene
Match: both `straining`. Results: winner `happy`, loser `crying`, DRAW both `idle`. Mascots/crests only via `<Mascot>`/`<Crest>`; rope and knot are CSS boxes.

## Navigation
HostMatch: authError/no token -> /host/login; `ended` -> /host/results/:id with the ended payload as router state; cancelled -> /host/create; reset -> /host/lobby/<newId>; snapshot LOBBY/FINISHED redirect to lobby/results. HostResults: analytics from router state, else GET analytics; "Nova Partida" -> reset -> /host/lobby/<newId>, on failure -> /host/create.

## Analytics tiles
Players, total pulls, duration, peak (value/s at t), final rope; per team: players, pulls, average per player, best, worst; Recharts area chart of pullsPerSecond (inter/gremio in theme colors); top-N leaderboard.

## PT-BR copy
"<Time> venceu a Corda Brava!", "Empate! Ninguém levou a corda.", "A corda foi arrastada até o fim!", "O tempo acabou.", "Nova Partida", tile labels above.

## Checks
vitest 49/49 passed (12 files); tsc clean; build OK (only chunk-size warning from recharts); eslint clean.

## Deviations
- DRAW: both mascots idle (no exhausted sprite exists).
- Particles skipped (optional). No sound hooks.
- Not visually verified in a browser/with a live match; PullsTimeline is mocked in the HostResults test (jsdom has no layout).
- Leaderboard shows only pctOfTeam; pctOfAll/pullsPerSec not displayed.

## Fix round 1
Commit `844df23`.
1. `useSmooth` stops re-arming rAF once |target - current| < 0.01 (snaps); the effect restarts on target change.
2. `knotLeftPercent` returns 50 when target <= 0; assertion added to the existing test.
3. HostResults: 409 from GET analytics redirects to /host/match/:id.
4. Leaderboard also shows pctOfAll ("% do total") and pullsPerSec ("/s").
5. Shake/scale decay when no tick arrives: skipped (not a one-liner).
Checks: vitest 49/49, tsc clean, build OK, eslint clean.
