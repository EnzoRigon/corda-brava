# Polish P6 report: stadium match screen

## Built
- `pages/HostMatch.tsx`: HUD panel (Inter crest/name/score left, Grêmio mirrored right, giant gold timer, red/blue power bar with gold marker driven by rope/target), live event feed, `RopeScene` with fx, moments, Cancel.
- `lib/matchFx.ts` (pure, tested): `pushEvents` (feed reducer), `leadChange`, `isFinalSeconds`. `lib/matchFx.test.ts`: 4 tests.
- `components/EventFeed.tsx`: per-team `<ul>` of pixel tags (player icon, NAME, lightning icon, +N), team colour; newest on top with a pop-in (keyed by entry id), rows 3+ at 70% opacity, 5+ at 40%. Sits between the mascots above the rope, under the HUD.
- `RopeScene` / `Rope`: dust puffs (P1 dust strip, `steps(5)`) at each mascot's heels, opacity/scale follow `delta/30`; sparkle burst (P1 sparkle strip) at the knot while a big swing is in flight (the existing `shake` flag); `pennant-red`/`pennant-blue` icon on the knot for the side it leans to. Styles in new `theme/match.css` (imported by HostMatch). `Timer` got an `urgent` prop.

## Feed logic
Per tick, each `tick.events` entry is pushed to its team list, newest first, capped at 6. A same-player entry within 400 ms is merged (counts add) and moved to the top. 400 ms is below the 500 ms tick on purpose: a wider window (tried 2.5 s) collapsed a continuously tapping player into one row with a huge "+107", which looked dead. Now each tick is its own row.

## Moments
- First RUNNING: "JÁ!" pop-in (1.4 s) + `whistle`.
- Lead change (`leadChange`, 5% of target dead-band so wobble near 0 is not a swing): "VIRADA!" red banner + `swing` sfx.
- Last 10 s (`isFinalSeconds`, driven by `useCountdown`): timer red + pulsing, red vignette pulse, `heartbeat` each second, `countdown` beep at 3, 2, 1.
- Cancel: ghost "Cancelar" bottom-left, confirm panel ("Sim, cancelar" / "Voltar"), calls `cancelMatch` then `/host/create`.
- `prefers-reduced-motion`: feed/dust/pennant/sparkle/banner/vignette/timer animations off. All motion is transforms/opacity/background-position.

## Ruling: no winning/losing mascot states in the rope scene
The brief asked to pass `winning`/`losing`. Tried it: the `happy`/`defeat` GIFs are 384x448 but the mascot is not holding the rope in them (Grêmio jumps with arms up, rope floats). That breaks rope alignment, so both sides stay `straining` (passed explicitly). Push-scale on delta still gives the strain feel. Happy/defeat remain for the results screen.

## Visual checks (own tab, 1280x720, 4 test matches via API + pull loop)
Checked: HUD, feed filling both columns and fading, dust at feet, pennant tracking the lean, sparkles at the knot during swings, last-10 s red timer + vignette, cancel confirm flow (match FINISHED, page went to /host/create), `JÁ!` banner present in DOM right after load (screenshot latency missed it visually). VIRADA fired no screenshot: the rig could not produce a crossing swing past the dead-band before a win; logic covered by unit test. Rope alignment measured with getBoundingClientRect: Inter img right edge == rope left (261.17), rope right == Grêmio img left (1019.57).
Fixed along the way: feed merge window (above); winning/losing sprites (above). Observation: server rate/normalization makes the rope drift slowly with a few test players; the feed 6th row sits just above the rope but does not touch it at 720p.

## Checks (frontend/)
`npm test -- --run` 17 files / 71 tests; `tsc --noEmit`, `npm run lint`, `npm run build` clean (chunk warning only); `npx playwright test` 1 passed (one earlier run flaked at the lobby `.join-url` assertion while P5 was editing; reran green). No selector changes.
