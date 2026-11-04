# Polish P3 report: pixel design system, scene on every screen, SFX

## Components (frontend/src/components)
- `GameBackground({variant, team?})`: fixed, `aria-hidden`, z-index 0. Layers: sky tile, 6 sparkle-strip stars (steps(6) + twinkle), moon, 2 drifting clouds, stadium strip (glow pulse), pitch (first 20 rows of the pitch strip + mowed-stripe fill + vignette), optional team tint (multiply, 0.28).
  Variants: `title` (login/create/lobby, pitch 24vh), `match` (pitch 44vh = `--pitch-h-match`), `results` (26vh), `player` (18vh, tinted by team). Integer scale `--s` = 2 / 3 (>=900px) / 4 (>=1500px).
- `AppLayout`: route layout (wraps all routes in App.tsx); `variantFor(pathname)`; player team read from `loadSession(id)`. Renders `GameBackground` + `MuteToggle` + `<Outlet/>`.
- `PixelButton({variant?: "primary"|"red"|"blue"|"ghost", ...button props})`: real `<button type=button>`, plays sfx `click`, press = translateY(4px) + shallower shadow. Class `pxbtn pxbtn-<variant>`.
- `PixelPanel({tone?: "red"|"blue", ...div props})`: class `pixel-panel`, notched corners (`--notch` clip-path) + stepped inset border.
- `Logo({scale=3, small=false})`: P1 logo (160x56 or 96x36) at integer scale, `alt="Corda Brava"`, `anim-bob`. Login wraps it in `<h1 class="logo-heading">`.
- `Icon({name, size=32, label?})`: 16 P1 icons (`heart star trophy crown lightning hourglass speaker-on speaker-off arrow-left check cross player whistle rope-coil pennant-red pennant-blue`); decorative unless `label`.
- `MuteToggle`: fixed top-right button, `aria-label="Silenciar sons"`, `aria-pressed`.

## SFX
`lib/sfx.ts`: `play(name)`, `isMuted()`, `setMuted(v)`, `subscribe`, `unlock()` (called on first pointerdown/keydown; AudioContext created lazily). Names: `click tap join countdown whistle swing heartbeat win draw`. Mute persisted in localStorage `cb.muted` (try/catch). No-op when muted, no AudioContext, or context not `running`. Master gain 0.18. `hooks/useSfx.ts` -> `{muted, play, toggleMute}`.
Wired: click (PixelButton), tap (PullButton), join (lobby, roster grows), whistle (HostMatch first RUNNING), win/draw (HostResults when analytics appear). `countdown`, `swing`, `heartbeat` exist but are not yet wired (P6).

## CSS (theme/design.css, imported after global.css in main.tsx)
Tokens `--ink --gold --night --pitch-h-match --s --notch`. Utilities: `.pixel-title`, `.sr-only`, `.anim-bob/-blink/-pop/-shake/-float-up`, `.form-panel`, `.qr-panel`, `.analytics-panel`, `.host-page.center`. Keyframes `cb-bob cb-blink cb-pop-in cb-shake(global.css) cb-float-up cb-twinkle cb-drift cb-confetti-fall cb-sprite-6 cb-glow`. `prefers-reduced-motion` disables drift/twinkle/glow/bob/blink/shake.
`.tile`, `.team-column`, `.result-banner` share the panel look. Match: `.match .rope-scene` is absolutely placed at `bottom: 0.6 * --pitch-h-match` with `--mascot-w: clamp(120px, min(24vw, 34vh), 400px)`; rope geometry still derives only from `--mascot-w`.

## Screens
Login (logo, panel, gold ENTRAR), create (OPCOES-style panel), lobby (logo, QR panel, team panels, join chime), match (HUD panel, mascots standing on grass under the stadium, rope continuous), results (banner panel, mascots over the stands, stat tiles), player join/wait/play (tinted scene, panels, beveled PUXAR button).

## Visual check (own browser pane, 800x600)
Checked login, create, lobby, running match, player play (tinted red), join, results. Fixed: moon sat behind the match HUD (moved lower for `match`), join-url too dim, unselected team-pick borders invisible. Rope alignment zoomed on both mascots: rope leaves both hands, continuous. Test matches 8WV6PH cancelled; FTY2N6 had finished (cancel 409). Known rough edges left for P4-P7: big PUXAR button covers the pitch, results mascots stand on the stands not grass, mascot on player play is small.

## Checks
`npm test -- --run` 15 files / 57 tests pass; `tsc --noEmit`, `npm run lint`, `npm run build` clean (chunk size warning only); `npx playwright test` 1 passed. No selector changes were needed.
