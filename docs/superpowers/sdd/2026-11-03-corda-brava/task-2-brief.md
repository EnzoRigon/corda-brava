### Task 2: Pure game rules (domain, fully unit-tested)

**Files:**
- Create: `backend/app/domain/rules.py`
- Test: `backend/tests/domain/test_rules.py`

**Interfaces:**
- Consumes: `MatchState`, `TickInput`, enums from Task 1.
- Produces (pure, no IO): `apply_pulls(state: MatchState, tick: TickInput, *, balance_mode, pull_unit, rope_target) -> MatchState` (returns new state with updated `rope_position`); `check_win(rope: float, rope_target: int) -> MatchResult | None`; `resolve_result(state, *, timed_out: bool) -> tuple[MatchResult, EndReason]`; helper `clamp(x, lo, hi)`.

- [ ] **Step 1:** Write tests covering: raw mode net delta `(pulls_gremio - pulls_inter)*PULL_UNIT`; normalized mode `effort=(pulls/max(count,1))*unit` then `delta=effort_gremio-effort_inter`; **0-player team → no NaN, contributes 0**; clamp at `±ROPE_TARGET`; `check_win` returns GREMIO at `>=+target`, INTER at `<=-target`, `None` between; `resolve_result` with `timed_out=True` and rope≠0 → `(DRAW, TIMEOUT)`; with rope at +target → `(GREMIO, WIN)`.
- [ ] **Step 2:** Run `pytest backend/tests/domain/test_rules.py -v` → FAIL.
- [ ] **Step 3:** Implement `rules.py` per `prompt.md §6` formulas exactly.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(domain): pure game rules (apply_pulls/check_win/resolve_result) + tests`.

