# Polish P4 report: host title, options, lobby

Commit: ce83ceb

## Built
- HostLogin = title screen: Logo scale 4 (bob), tagline, blinking PRESSIONE START, always-visible password panel (label "Senha do host"), gold ENTRAR, red pixel toast (`.px-toast`) for 401/429/errors.
- HostCreate = OPCOES: panel "NOVA PARTIDA", − / + stepper (30 s steps, clamped 30..600, m:ss + hourglass), number input kept with label "Duração (segundos)", Normalizado/Bruto toggle with one-line hint (API supports balanceMode), gold "Criar partida", back arrow to login. Exports stepDuration/fmtDuration.
- HostLobby: small logo; 3-column grid (Inter vestiário | framed QR with blinking "APONTE A CÂMERA" + .join-url | Grêmio vestiário); TeamColumn now has a team-color header with crest, name, count; PlayerIcon tiles pop in (join sfx already wired); pulsing gold "Iniciar partida" disabled with "Aguardando jogadores…" hint at 0 players; "Um time está sem jogadores" warning when exactly one side is empty (start still allowed). Stacks to one column under 1000px.
- Styles in new theme/host.css; reduced-motion disables pulse and countdown animation.

## Start / countdown ordering
Click -> 3-2-1 overlay (700 ms per tick, countdown sfx, ~2.1 s) -> startMatch API -> navigate to /host/match. The server timer starts only at the API call, so the countdown costs no play time. API error hides the overlay and shows the toast (401 goes to login).

## Visual check (own tab, 1280x720 emulation, effective ~800x450)
Login (also wrong password toast), create, lobby empty and with 3+1 players, countdown. Fixed: team count wrapped in header, QR/join URL cramped and overflowing short viewports (QR sized by vh, smaller URL font), player names truncated too hard, warning toast was fixed-position (now inline), countdown digit started at opacity 0 (now scale-only animation). The embedded pane throttles CSS animation, so the digit was verified via computed style (opacity 1), not a screenshot. Test matches cancelled.

## Checks
npm test: 18 files / 75 tests pass (new: stepper bounds/step/format, empty-team warning, start disabled with no players); tsc, lint, build clean; playwright 1 passed.
