### Task 16: Host Match scene (rope + mascots + timer, interpolation) + Results + analytics charts

**Files:**
- Create: `frontend/src/pages/HostMatch.tsx`, `HostResults.tsx`, `frontend/src/components/RopeScene.tsx`, `Rope.tsx`, `Timer.tsx`, `ResultBanner.tsx`, `AnalyticsGrid.tsx`, `frontend/src/components/charts/PullsTimeline.tsx`, `frontend/src/hooks/useCountdown.ts`
- Test: `frontend/src/components/RopeScene.test.tsx`

**Interfaces:**
- Consumes: useHostSocket, Mascot/Crest, Recharts, analytics types.
- Produces: HostMatch — `RopeScene` with both mascots (`straining`, intensity scaling with `delta`), knot position from `rope` (`left% = 50 + rope/target*40`, rAF interpolation toward latest tick), `Timer` (`useCountdown` visual interpolation of `remainingS`), juice (shake on big swing, +particles optional). HostResults — winner mascot `happy`, loser `crying` (draw: both exhausted), `ResultBanner` PT-BR, `AnalyticsGrid` tiles + `PullsTimeline` Recharts line/area from `analytics`, "Nova Partida" → reset→create.

- [ ] **Step 1:** Write `RopeScene.test.tsx`: given `rope=-100 target=100` the knot style left ≈ `10%`; `rope=+100` ≈ `90%`; `rope=0` ≈ `50%`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement scene, interpolation, results, charts.
- [ ] **Step 4:** Run → PASS; `tsc` + `npm run build` clean.
- [ ] **Step 5:** Commit `feat(frontend): host match rope scene + results + analytics charts`.

---

