# Task 2 Report — Pure Game Rules

## Status: DONE

## Commit
`ee177b5` — feat(domain): pure game rules (apply_pulls/check_win/resolve_result) + tests

## Files Created
- `backend/app/domain/rules.py` — pure functions, no IO/framework imports
- `backend/tests/domain/__init__.py` — empty package marker
- `backend/tests/domain/test_rules.py` — 35 unit tests

## Final Signatures

```python
def clamp(x: float, lo: float, hi: float) -> float: ...

def apply_pulls(
    state: MatchState,
    tick: TickInput,
    *,
    balance_mode: BalanceMode,
    pull_unit: float,
    rope_target: int,
) -> MatchState: ...

def check_win(rope: float, rope_target: int) -> MatchResult | None: ...

def resolve_result(
    state: MatchState,
    *,
    timed_out: bool,
    rope_target: int,
) -> tuple[MatchResult, EndReason]: ...
```

## Key Decisions

### resolve_result and timed_out
`resolve_result` first calls `check_win`. If a win threshold was already crossed (rope == ±rope_target), it returns `(winner, WIN)` regardless of `timed_out`. Only if no threshold was crossed does it fall through to `(DRAW, TIMEOUT)`. This ensures that a match where the rope reaches the boundary *and* the clock expires at the same moment is still reported as a WIN (the threshold takes priority).

### normalized mode divide-by-zero
`max(player_count_team, 1)` guards both teams independently so zero-player teams contribute a raw `(pulls / 1) * pull_unit` rather than NaN. In practice a team with zero players should have zero pulls too, making their effort 0 regardless.

### Immutability
`apply_pulls` uses `state.model_copy(update={"rope_position": new_rope})` (Pydantic v2 API) — never mutates the input object. Tests explicitly assert the input `rope_position` is unchanged after the call.

## Test Results
```
35 passed in 0.13s
ruff check — all checks passed
black --check — 3 files would be left unchanged
```

## Coverage Map
| Requirement | Test(s) |
|---|---|
| raw delta `(gremio-inter)*unit` | `TestApplyPullsRaw::test_positive_delta_gremio_leads`, `test_negative_delta_inter_leads` |
| normalized `effort=pulls/max(count,1)*unit` | `TestApplyPullsNormalized::test_small_team_beats_lazy_big_team` |
| 0-player team, no NaN | `test_zero_players_gremio_no_nan`, `test_zero_players_zero_pulls_inter_contributes_zero` |
| clamp at ±target | `test_clamp_at_positive_target`, `test_clamp_at_negative_target`, `test_normalized_clamp_at_positive_target` |
| check_win boundary inclusive | `test_float_boundary_inclusive_gremio`, `test_float_boundary_inclusive_inter` |
| check_win None in mid-range | `test_rope_in_center_no_winner`, `test_rope_just_below_positive_target_no_winner` |
| resolve_result: timed_out, no threshold → DRAW,TIMEOUT | `test_timed_out_no_threshold_gives_draw`, `test_timed_out_center_rope_draw` |
| resolve_result: threshold → WIN | `test_rope_at_positive_target_not_timed_out_gremio_wins`, `test_rope_at_negative_target_not_timed_out_inter_wins` |
| resolve_result: threshold beats timed_out | `test_timed_out_with_rope_at_gremio_side_gremio_wins`, `test_timed_out_with_rope_at_inter_side_inter_wins` |
| immutability | `TestApplyPullsImmutability::test_input_state_unchanged`, `test_returns_new_object` |
