# Polish P5 report: player phone screens

## Built (frontend, new CSS in `theme/player.css`, imported in main.tsx)
- **Join**: small logo, two big team cards (crest 96, name in team color, player icon + count); selected card scales, tints and glows. Name field in a PixelPanel, gold ENTRAR, errors in a red pixel toast (`role=alert`). Collaborator's behavior (public polling, session redirect) untouched.
- **Wait**: team crest (bob) + idle mascot, panel "Aguardando o host iniciar..." with blinking dots (dots are aria-hidden so the heading text stays for the E2E), teammate icons + count from `/public` polling (no new endpoint).
- **Play**: darkened team-color screen with stripes, crest 160 pulsing per tap, big tap counter, combo bar + "COMBO xN" with lightning icon, giant PUXA! (45dvh, 12px press depth). "+1" pops spawn at the touch point. Per tap: `tap` sfx (mute respected) and `navigator.vibrate(8)` (guarded, always on). usePullBuffer/PullButton semantics unchanged (pointerdown, keyboard click detail 0 only, no double fire, `touch-action: manipulation`, no selection).
- **End**: banner VITÓRIA! (team color, confetti from the P1 sheet) / DERROTA… (dimmed scene) / EMPATE! / Partida cancelada; mascot happy/crying/idle; "Você puxou N vezes!" from local storage; "Obrigado por jogar!" kept; `win`/`draw` sfx on mount.
- Reduced motion disables glow, dots, banner pop, pops and confetti.

## Combo logic (`lib/combo.ts`, pure)
Meter m in [0,1]. Tap: `m = min(1, m + 0.1)`. Decay 0.4/s (PlayerPlay ticks every 100 ms while m > 0). About 4 taps/s holds steady; faster climbs, slower fades. Shown when m >= 0.15 as level `1 + floor(9m)` (1..10).

## Local tap count (`lib/localPulls.ts`)
`localStorage cb.pulls.<matchId>`; Play starts from the stored value (survives reload) and saves total on each change; End reads it. Hidden when 0 or cancelled.

## Tests
New: `lib/combo.test.ts` (build, cap, decay, steady-rate, localPulls round trip); `PlayerEnd.test.tsx` rewritten (cancelled, win+confetti, lose+dim, draw, local count). Copy changed: win/lose titles ("Seu time venceu/perdeu!" -> VITÓRIA!/DERROTA…) and the E2E button name PUXAR -> PUXA!.

## Visual check (390x844 emulation, own tab)
Checked Join (empty, Grêmio selected), Wait, Play (Inter and Grêmio, mid-combo x7 / x9, decaying), End draw, lose, win with confetti. Fixed: Play button was the same red as the page (made the screen a darker shade of the team color), crest enlarged to 160 to fill the gap, unselected cards were too dim. Screenshots from the shared pane were low-res (pane size); layout verified by rect (button 358x368 at y 456-824).

## Checks
`npm test -- --run` 17 files / 72 tests pass; `tsc --noEmit`, `npm run lint`, `npm run build` clean (chunk warning only); `npx playwright test` 1 passed.
