# Polish P7 report: results "game over" screen

## Built
- `ResultBanner`: "FIM DE JOGO" (.pixel-title, drops in), result line "INTER VENCEU!" / "GRÊMIO VENCEU!" (team colour) / "EMPATE!" (gold) / "PARTIDA CANCELADA"; reason "Corda puxada até o fim!" / "O tempo acabou!". `.result-banner` kept.
- Podium in `HostResults`: winner Mascot happy on a tall block with bobbing crown, loser crying on a low block, draw/cancelled idle at equal height. Mascots sized by width (192, height auto), columns bottom-aligned so feet sit on the block tops; crests + names on the block fronts.
- `Confetti` got a `colors` prop (sheet used as CSS mask, tinted); 36 pieces in winner colours, gold on draw, none when cancelled; hidden under reduced motion.
- `AnalyticsGrid`: PixelPanel stat tiles with icons (pulls, duration, peak, final rope pennant), per-team cards (players, pulls, average, MVP with crown + name + pulls), chart panel, retro RANKING table (top 5: pos, team dot, name, pulls, % total, /s; heading text "Ranking" kept).
- `PullsTimeline`: Line chart, `stepAfter`, team colours, pixel font axes/legend/tooltip, square dark tooltip, dark panel.
- `PlayAgain` ("JOGAR DE NOVO?"): SIM (gold, existing reset -> lobby flow with /host/create fallback) / NÃO (ghost -> /host/create); arrows move a blinking ▶, Enter confirms (a focused button handles Enter natively to avoid double fire).
- Staggered entrance title -> podium -> stats; reduced motion disables it. Styles in new `theme/results.css`.

## Tests
ResultBanner (each result line, reasons, cancelled), HostResults (copy, mascots, cancelled has no confetti, win/draw have confetti, MVP per team), PlayAgain (arrow selection + Enter). 80 tests total.

## Visual checks (own tab 1280x720, real matches via API)
Win (Inter), draw. Fixed: confetti drew over the panels (z-index), podium block too short so the loser's name collided with the mascot's feet (taller blocks, content bottom-aligned), page opened scrolled (scroll restoration only affected my reload). Also Vite served a stale empty PullsTimeline module after the rewrite until files were touched (dev-server cache only). Page is ~1960px tall; title+podium fill the first fold, stats/ranking/prompt below by scroll.

## Checks (frontend/)
vitest 19 files / 80 tests, tsc, lint, build clean. Playwright: first run failed once (cause not captured; likely cold dev server after build), reran twice green.

Commit: c3bc36c
