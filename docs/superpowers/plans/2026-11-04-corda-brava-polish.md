# Corda Brava — Front-end polish plan (game design pass)

Owner request (2026-11-04): polish every screen into a real retro game — pixel-art context in the
whole UI, motion, effects, **sound**, a rethought player screen (team icon, animated), rethought
login/title, match and end screens, and a live **event feed** (last N pulls per side) on the match
screen. Use the **pixel-art-studio** skill for icons and art. References: pixel title screens
("PIXEL ZONE", "RIVER LAND", "GAME OVER / TRY AGAIN?", "PORTFOLIO … START") — chunky outlined
pixel lettering, layered painterly pixel backgrounds, beveled pixel buttons, heart/coin HUD icons.

Executed like the main plan: one implementer subagent per task (sonnet), review gate, fix loop,
ledger entry in `docs/superpowers/sdd/2026-11-03-corda-brava/progress.md` under "POLISH PHASE".

## Art direction (applies to every task)

- **Setting:** a night match at a pixel stadium. Deep navy sky with twinkling stars and a moon,
  distant stadium silhouette with floodlights, a grass pitch strip with chalk lines in front.
  Layered (sky → stars → clouds → stadium → pitch) with slow parallax drift.
- **Title/logo:** "CORDA BRAVA" as a pixel-art image (chunky letters, dark outline, drop shadow,
  gold/cream face — neutral, not a club palette), a rope running between the two words.
- **UI kit:** beveled pixel buttons (light top-left edge, dark bottom-right, 4px press-down),
  pixel panels/frames (stepped corners via box-shadow), Press Start 2P everywhere, stepped
  text-shadow for big headings, blinking "PRESSIONE START"-style prompts.
- **Team identity:** Inter red `#E5050F`, Grêmio blue `#0D80BF` / `#4FA9DC` + black. Team UI uses
  colors, the owner's crest files and original generic pennants/flags.
- **Art policy (unchanged, must hold):** Saci / Mosqueteiro and the club crests come **only** from
  the owner's image files via `<Mascot>` / `<Crest>`. New pixel art is original and generic
  (icons, scenery, particles, logo lettering) — never a drawing of the club characters or crests.
- **Motion:** transforms/opacity only, 60fps, `prefers-reduced-motion` respected (disable shake,
  parallax and particles).
- **Sound:** synthesized chiptune SFX with Web Audio (no audio files): tap blip, player-join chime,
  countdown beeps, start whistle, rope swing whoosh, last-10-seconds heartbeat, win fanfare,
  draw jingle, UI click. Global mute toggle (speaker icon) persisted in localStorage; audio is
  unlocked on the first user gesture. Host default ON, player default ON at lower volume.
- **Copy:** PT-BR, short and punchy (e.g. "PRESSIONE START", "PUXA!", "FIM DE JOGO",
  "INTER VENCEU!", "EMPATE!", "JOGAR DE NOVO?").

## Tasks

### P1 — Pixel asset pack (pixel-art-studio)
Build scripts under `.claude/skills/pixel-art-studio/pixel-art/corda-brava-ui/`, exports (1x PNG,
CSS scales them with `image-rendering: pixelated`) to `frontend/src/assets/ui/`.
- Logo "CORDA BRAVA" (~160×56) + small variant.
- Icons 16×16: heart, star, trophy, crown, lightning, hourglass, speaker-on, speaker-off,
  arrow-left, check, cross, player, whistle, rope coil, pennant (red + blue variants).
- Particles: sparkle (anim strip), dust puff (anim strip), confetti pieces.
- Scenery: night-sky tile with stars (tileable), moon, 2 clouds, stadium silhouette strip with
  floodlights (tileable horizontally), pitch/grass strip with chalk line (tileable).
- Follow the skill loop (preview → look → critique → fix, ≥2 passes). Contact sheet preview
  committed in the build folder.

### P2 — Backend: per-tick event list for the feed (parallel with P1, disjoint files)
- WS `tick` gains `events: [{playerId, name, team, count}]` — one entry per pull batch applied in
  that tick (names from the roster). Bounded (cap ~20 per tick). Tests updated.
- Frontend type `TickMsg.events` added.

### P3 — Design system: background scene, UI kit, SFX engine
- `GameBackground` (layers + parallax + twinkle, variants: title / lobby / match / results).
- `PixelButton`, `PixelPanel`, `PixelTitle`/`Logo`, `Icon` (asset map), `MuteToggle`.
- `sfx` module (Web Audio synth, all sounds above) + `useSfx()`; tests for mute persistence and
  that calls are no-ops when muted / AudioContext missing.
- Global CSS tokens + keyframes (bob, blink, pop-in, shake, float-up, confetti fall).

### P4 — Title/host screens: Login, Create, Lobby
- Login = title screen (logo, scene, blinking "PRESSIONE START", password panel, START button).
- Create = "OPÇÕES" menu panel (duration stepper, scoring mode toggle), pixel buttons.
- Lobby = QR in a pixel frame, two team "vestiários" panels with crest + pennant, players pop in
  with a chime, live counts with icons, big pulsing INICIAR.

### P5 — Player screens: Join, Wait, Play, End
- Join: team picker as two big cards (crest, team color, count), name field panel.
- Wait: team-colored scene, team crest + animated mascot (idle bob), "Aguardando o host…" dots,
  teammates count.
- Play: full team-color screen, crest at top, giant beveled PUXA! button with press depth,
  "+1" pops, combo meter, tap blip + light haptic (`navigator.vibrate`), mascot straining.
- End: big win/lose/draw banner, mascot happy/crying, confetti on win, "Você puxou N vezes"
  (local count only — no server analytics on the phone).

### P6 — Match screen + event feed
- Stadium scene, HUD (crests, names, score bars, giant timer), larger mascots, rope with knot flag,
  dust particles at the knot, shake on big swings, lead-change flash, red pulse + heartbeat in the
  last 10 s, start whistle + "JÁ!" flash when RUNNING begins.
- Event feed: last N (≈6) events per side in two columns, newest slides in at the top
  ("PAULO +12"), fades out.

### P7 — Results screen
- "FIM DE JOGO" + "INTER VENCEU!" / "EMPATE!" chunky title, confetti in winner colors, winner
  mascot happy on a podium, loser crying, fanfare. Stats as pixel cards (MVP with crown per team,
  peak, totals), pixel-styled chart, "JOGAR DE NOVO?" → Nova Partida.

## Constraints for every task
- Keep `npm test -- --run`, `npx tsc --noEmit`, `npm run lint`, `npm run build` green; keep the
  Playwright E2E green (update its selectors in the same task if copy changes).
- No new UI/animation/sound libraries; CSS + Web Audio only.
- Dev servers may be running on :8000/:5173 — never stop them.
