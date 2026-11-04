# Task 15 Report — useHostSocket + Host Login/Create/Lobby

**Status:** DONE. Code commit: see `git log` (feat(frontend): useHostSocket + host login/create/lobby).

## Files
hooks/useHostSocket.ts (+test, 8 tests), pages/HostLogin.tsx (+test, 2), HostCreate.tsx, HostLobby.tsx, components/QRCode.tsx, TeamColumn.tsx, PlayerIcon.tsx; App.tsx routes wired; global.css host styles; dep `qrcode.react` (named by prompt.md).

## Hook: `useHostSocket(matchId, token)` returns
`{status, snapshot, lastTick, ended, terminal, connected, authError}`
- `snapshot: MatchView|null` kept live: `player_joined` appends (dedupe by id), `tick` updates rope/remainingS/scores/status RUNNING, `ended` sets FINISHED/result/endReason/rope=finalRope.
- `ended: EndedMsg|null` (includes `analytics`); `terminal: CancelledMsg|ResetMsg|null` (reset has `newMatchId`); `authError` true after close 1008.
- Task 16 HostMatch/HostResults consume this directly (HostResults can read `ended.analytics`).

## Reconnect / terminal rules
Reconnect only on unexpected close: backoff 500ms * 2^n, cap 5000ms, reset on open. Never after close 1008 (sets authError), nor after `ended`/`cancelled`/`reset`, nor unmount. A fresh server snapshot on reconnect replaces state. Effect cleanup closes socket and clears timer on unmount / matchId or token change.

## Token storage
`sessionStorage["cb.hostToken"]` (try/catch); exported `HOST_TOKEN_KEY`, `getHostToken()` from pages/HostLogin.tsx. Missing token, 401, or authError -> /host/login.

## QR + joinUrl
`qrcode.react` (QRCodeSVG). Click opens fullscreen overlay (QR + URL); Esc or click closes. joinUrl: HostCreate passes the backend `joinUrl` via router state; GET /matches/:id has no joinUrl, so on reload the lobby falls back to `${PUBLIC_BASE}/j/${id}` (VITE_PUBLIC_BASE, else window origin). Matches backend format `base/j/<id>`.

## PT-BR copy
Corda Brava, Senha do host, Entrar, Nova partida, Duração (segundos), Pontuação, Normalizada (equilibra times), Bruta (cada puxada vale 1), Criar partida, Entre 30 e 600 segundos, Escaneie para entrar, Iniciar partida, N jogador(es), Ampliar QR code, Clique ou pressione Esc para fechar. API detail (incl. 429) shown verbatim.

## Art policy
PlayerIcon is a generic colored block with the player's initial. Crests only via `<Crest>`. No mascot used in these pages.

## Checks (frontend/)
vitest 8 files / 41 tests pass; tsc clean; lint clean; build OK.

## Deviations
- Start button disabled until at least one player has joined (not in the brief).
- Duration bounds 30-600 hardcoded in HostCreate (mirror backend defaults).
- Lobby routes to /host/create on cancelled/reset (reset's newMatchId not followed; Task 16 may handle).
- Tests for the hook written in the same pass, not watched failing first. Not verified in a real browser.

## Fix round 1 (commit 1a152d4)
- Backend: `MatchView.joinUrl` (optional) set in `match_view()` via shared `_join_url()` (same as create), so GET and WS snapshot carry it; test added. `create_app(settings=None)` falls back to `get_settings()` (README uvicorn --factory command works).
- Frontend: lobby joinUrl = snapshot.joinUrl > router state > VITE_PUBLIC_BASE fallback (supersedes the QR/joinUrl note above). Socket cleanup nulls onmessage/onopen; JSON.parse guarded. QR overlay: aria-modal, tabIndex -1, focused on open, focus returns to QR button. `reset` navigates to /host/lobby/<newMatchId>; cancelled still goes to /host/create. New HostLobby test.
- Checks: backend pytest 144 pass, ruff and black clean; frontend vitest 9 files / 42 tests, tsc, build, lint clean.
