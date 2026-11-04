# Task 12 Report — Owner assets + Mascot/Crest components

**Status:** DONE. Code commit: `7c253ad`

## Files
- `frontend/src/assets/mascots/` — 10 files (`{saci,mosq}_{master.png,pull.gif,happy.gif,defeat.gif,cry.gif}`)
- `frontend/src/assets/crests/{inter,gremio}.png`
- `frontend/src/components/Mascot.tsx`, `Crest.tsx`, `Mascot.test.tsx`

Assets are verbatim `cp` copies; `cmp` against the originals matched 12/12 (byte-identical). No code draws characters or crests; they are imported files shown as `<img>`.

## Props
- `<Mascot team: TeamId, state: MascotState, size?: number = 128, className? />`
- `<Crest team: TeamId, size?: number = 48, className? />`
- `TeamId` is lowercase ("inter" | "gremio"), not the brief's `INTER`.

## State to sprite
| state | sprite |
|---|---|
| idle | *_master.png |
| straining | *_pull.gif |
| winning, happy | *_happy.gif |
| losing | *_defeat.gif |
| crying | *_cry.gif |

Saci = inter, mosq = gremio. Alt text: "Saci (Inter)", "Mosqueteiro (Grêmio)", "Escudo do Inter/Grêmio". `image-rendering: pixelated`.

## Mirroring
Per the owner prototype (`index.html`: `.fighter.gremio{transform:scaleX(-1)}`), sprites face right and only Grêmio is mirrored (`scaleX(-1)`) to face center.

## Checks (frontend/)
test 7/7 pass; tsc clean; build OK; lint clean.

## Deviations
- Lowercase team ids. No @testing-library installed, so tests use `react-dom/server` `renderToStaticMarkup`; Vite asset imports resolve to paths in vitest.
- "draw" has no state; callers pass `idle` (master), as the design doc says.
