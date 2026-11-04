# Task 18 Report — READMEs + Playwright E2E + validation loop

**Status:** DONE (Docker step not run) — code commit 5126670

## Files
- Created: `frontend/playwright.config.ts` (baseURL `E2E_BASE_URL` or :5173, chromium only, no webServer), `frontend/e2e/flow.spec.ts`, `backend/README.md`, `frontend/README.md`.
- Modified: root `README.md` (status, run/Docker/LAN/flow/Azure swap/VPS-TLS/scaling/e2e), `frontend/package.json` (`e2e` script, `@playwright/test` devDep), `frontend/vitest.config.ts` (exclude `e2e/**`), `.gitignore` (playwright-report/, test-results/).

## E2E steps and selectors
1. Host: `/host/login`, label "Senha do host", button "Entrar"; label "Duração (segundos)" = 30, button "Criar partida"; URL `/host/lobby/<id>`; joinUrl read from `.join-url` text.
2. Player (separate context): open joinUrl path, label "Seu nome", radio /Inter/, button "Entrar", heading "Aguardando o host iniciar".
3. Host: `.team-roster` contains player name; button "Iniciar partida".
4. Player taps "PUXAR" via `pointerdown` events (button reacts to pointerdown); host `data-testid="knot"` (already existed) `style.left` moves away from 50%.
5. Match ends (timeout at 30 s since taps stop after the knot moves); player sees "Obrigado por jogar!".
6. Host on `/host/results/`: `.result-banner`, heading "Ranking", player name.
Test creates its own match; host password from `E2E_HOST_PASSWORD` (default dev password).

## App bugs found
None. Green on first run; no frontend source changes, no data-testid additions.

## Validation loop
1. backend: ruff clean, black clean, pytest 144 passed.
2. frontend: lint clean, tsc clean, vitest 49 passed (12 files; e2e excluded), build OK.
3. Docker: NOT RUN (Docker not installed). Compose files and README Docker instructions unverified at runtime.
4. Playwright: 1 passed (~34 s) against http://localhost:5173 (running uvicorn :8000 + Vite).

## Not verified
Docker prod/dev stacks, E2E against the nginx stack (:80), the win-by-rope path of the E2E (ended by timeout), real phones/LAN QR, TLS/wss deployment guidance.

## Deviations
Chromium downloaded via `npx playwright install chromium` (official CDN). E2E ends the match by timeout rather than by win.
