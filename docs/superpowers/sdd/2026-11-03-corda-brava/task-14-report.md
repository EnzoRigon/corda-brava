# Task 14 Report — Player flow (Join/Wait/Play/End)

**Status:** DONE. Code commit: 9cd6e92

## Files
- frontend/src/pages/PlayerJoin.tsx, PlayerWait.tsx, PlayerPlay.tsx, PlayerEnd.tsx
- frontend/src/components/PullButton.tsx
- frontend/src/hooks/useMePolling.ts (also exports loadSession/saveSession)
- Tests: pages/PlayerJoin.test.tsx (5), hooks/useMePolling.test.ts (3)
- Modified: App.tsx (4 /j routes), theme/global.css (player styles, +1 keyframes)

## localStorage session
Key `cb.session.<matchId>`, value `{playerId, playerToken, team}` (team lowercase). All access in try/catch. Cleared on /me 401/403.

## Polling / navigation
- Wait/Play/End each call `useMePolling(matchId, page)`: poll /me immediately, then every 1000ms (ME_POLL_MS); stops on unmount.
- If /me.screen != page: navigate (replace) to /j/:id/<screen>. Reload restores via stored token.
- No session, or 401/403: clear session, go to /j/:id. Other errors: keep polling.
- Join with stored session goes to /j/:id/wait; wait's polling forwards to the true screen. Successful join also navigates to wait (same mechanism).

## PT-BR copy
Entrar na partida, Seu nome, Escolha seu time, "<n> jogadores", Entrar, Digite seu nome., Escolha um time., Aguardando o host iniciar, PUXAR, Puxadas: N, Seu time venceu!/perdeu!, Empate!, Obrigado por jogar!. API detail shown verbatim on join errors (e.g. A partida já começou).

## Mascot state mapping
Join: crests only. Wait: idle. Play: straining. End: happy (own team won), crying (lost), idle (DRAW or result not yet loaded).

## PullButton
Real button; fires on pointerdown (preventDefault avoids synthetic click double-fire); onClick fires only when detail===0 (keyboard). +1 is a CSS keyframe span removed on animationend. usePullBuffer flush 500ms, enabled only when /me.screen==="play".

## Checks (frontend/)
npm test -- --run: 5 files, 25 tests pass. tsc --noEmit clean. npm run lint clean. npm run build OK.

## Deviations
- Tests were written after the implementation in the same pass (not watched failing first).
- Join/stored-session always route via /wait rather than calling /me directly in Join; polling does the hop.
- Join pick uses role=radio buttons (no native radios).
- Not verified on a real phone / in a browser.
