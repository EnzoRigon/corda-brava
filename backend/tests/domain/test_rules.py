"""Unit tests for pure game rules (app.domain.rules).

All tests are pure — no IO, no framework, no DB.
"""

import pytest

from app.domain.entities import MatchState, TickInput
from app.domain.enums import BalanceMode, EndReason, MatchResult, MatchStatus
from app.domain.rules import apply_pulls, check_win, clamp, resolve_result

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROPE_TARGET = 100


def _state(rope: float = 0.0) -> MatchState:
    """Return a minimal MatchState with the given rope_position."""
    return MatchState(
        match_id="TEST01",
        status=MatchStatus.RUNNING,
        rope_position=rope,
    )


# ---------------------------------------------------------------------------
# clamp
# ---------------------------------------------------------------------------


class TestClamp:
    def test_below_lower_bound_returns_lo(self) -> None:
        assert clamp(-200.0, -100.0, 100.0) == -100.0

    def test_above_upper_bound_returns_hi(self) -> None:
        assert clamp(200.0, -100.0, 100.0) == 100.0

    def test_within_range_unchanged(self) -> None:
        assert clamp(42.5, -100.0, 100.0) == 42.5

    def test_exactly_at_lower_bound(self) -> None:
        assert clamp(-100.0, -100.0, 100.0) == -100.0

    def test_exactly_at_upper_bound(self) -> None:
        assert clamp(100.0, -100.0, 100.0) == 100.0

    def test_zero_range(self) -> None:
        assert clamp(5.0, 3.0, 3.0) == 3.0


# ---------------------------------------------------------------------------
# apply_pulls — RAW mode
# ---------------------------------------------------------------------------


class TestApplyPullsRaw:
    def test_positive_delta_gremio_leads(self) -> None:
        """raw: tick(inter=3, gremio=5), pull_unit=1.0 → delta=+2 → rope 0→2."""
        tick = TickInput(pulls_inter=3, pulls_gremio=5)
        state = _state(0.0)
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert new.rope_position == pytest.approx(2.0)

    def test_negative_delta_inter_leads(self) -> None:
        """raw: inter=5, gremio=3 → delta=-2 → rope 0→-2."""
        tick = TickInput(pulls_inter=5, pulls_gremio=3)
        state = _state(0.0)
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert new.rope_position == pytest.approx(-2.0)

    def test_equal_pulls_no_movement(self) -> None:
        tick = TickInput(pulls_inter=4, pulls_gremio=4)
        state = _state(10.0)
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert new.rope_position == pytest.approx(10.0)

    def test_pull_unit_scales_delta(self) -> None:
        """pull_unit=0.5 halves the raw contribution."""
        tick = TickInput(pulls_inter=2, pulls_gremio=4)
        state = _state(0.0)
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=0.5, rope_target=ROPE_TARGET
        )
        # (4-2)*0.5 = 1.0
        assert new.rope_position == pytest.approx(1.0)

    def test_clamp_at_positive_target(self) -> None:
        """Rope near +target; big delta must not exceed rope_target."""
        tick = TickInput(pulls_inter=0, pulls_gremio=50)
        state = _state(90.0)  # 10 from boundary
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert new.rope_position == pytest.approx(float(ROPE_TARGET))

    def test_clamp_at_negative_target(self) -> None:
        """Rope near -target; big delta must not go below -rope_target."""
        tick = TickInput(pulls_inter=50, pulls_gremio=0)
        state = _state(-90.0)
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert new.rope_position == pytest.approx(-float(ROPE_TARGET))


# ---------------------------------------------------------------------------
# apply_pulls — NORMALIZED mode
# ---------------------------------------------------------------------------


class TestApplyPullsNormalized:
    def test_small_team_beats_lazy_big_team(self) -> None:
        """normalized: inter=10/5players → 2.0; gremio=6/2players → 3.0; delta=+1."""
        tick = TickInput(pulls_inter=10, players_inter=5, pulls_gremio=6, players_gremio=2)
        state = _state(0.0)
        new = apply_pulls(
            state,
            tick,
            balance_mode=BalanceMode.NORMALIZED,
            pull_unit=1.0,
            rope_target=ROPE_TARGET,
        )
        assert new.rope_position == pytest.approx(1.0)

    def test_zero_players_gremio_no_nan(self) -> None:
        """players_gremio=0 → max(0,1)=1 → no ZeroDivision / NaN."""
        tick = TickInput(pulls_gremio=4, players_gremio=0, pulls_inter=0, players_inter=5)
        state = _state(0.0)
        new = apply_pulls(
            state,
            tick,
            balance_mode=BalanceMode.NORMALIZED,
            pull_unit=1.0,
            rope_target=ROPE_TARGET,
        )
        # effort_gremio = (4/1)*1.0 = 4.0; effort_inter = (0/5)*1.0 = 0.0
        assert new.rope_position == pytest.approx(4.0)
        assert not (new.rope_position != new.rope_position)  # not NaN

    def test_zero_players_zero_pulls_inter_contributes_zero(self) -> None:
        """players_inter=0, pulls_inter=0 → contributes 0.0 (finite)."""
        tick = TickInput(pulls_inter=0, players_inter=0, pulls_gremio=3, players_gremio=3)
        state = _state(0.0)
        new = apply_pulls(
            state,
            tick,
            balance_mode=BalanceMode.NORMALIZED,
            pull_unit=1.0,
            rope_target=ROPE_TARGET,
        )
        # effort_inter = 0/1 * 1.0 = 0; effort_gremio = 3/3 * 1.0 = 1.0
        assert new.rope_position == pytest.approx(1.0)

    def test_normalized_clamp_at_positive_target(self) -> None:
        """Normalized mode also clamps at +rope_target."""
        tick = TickInput(pulls_gremio=1000, players_gremio=1, pulls_inter=0, players_inter=1)
        state = _state(float(ROPE_TARGET) - 1.0)
        new = apply_pulls(
            state,
            tick,
            balance_mode=BalanceMode.NORMALIZED,
            pull_unit=1.0,
            rope_target=ROPE_TARGET,
        )
        assert new.rope_position == pytest.approx(float(ROPE_TARGET))


# ---------------------------------------------------------------------------
# apply_pulls — immutability
# ---------------------------------------------------------------------------


class TestApplyPullsImmutability:
    def test_input_state_unchanged(self) -> None:
        """apply_pulls must not mutate the input MatchState."""
        tick = TickInput(pulls_inter=3, pulls_gremio=7)
        state = _state(0.0)
        original_rope = state.rope_position
        apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert state.rope_position == original_rope

    def test_returns_new_object(self) -> None:
        tick = TickInput(pulls_inter=1, pulls_gremio=1)
        state = _state(0.0)
        new = apply_pulls(
            state, tick, balance_mode=BalanceMode.RAW, pull_unit=1.0, rope_target=ROPE_TARGET
        )
        assert new is not state


# ---------------------------------------------------------------------------
# check_win
# ---------------------------------------------------------------------------


class TestCheckWin:
    def test_rope_at_positive_target_gremio_wins(self) -> None:
        assert check_win(100.0, ROPE_TARGET) == MatchResult.GREMIO

    def test_rope_above_positive_target_gremio_wins(self) -> None:
        # Should not happen after clamp, but check_win is robust
        assert check_win(150.0, ROPE_TARGET) == MatchResult.GREMIO

    def test_rope_at_negative_target_inter_wins(self) -> None:
        assert check_win(-100.0, ROPE_TARGET) == MatchResult.INTER

    def test_rope_below_negative_target_inter_wins(self) -> None:
        assert check_win(-150.0, ROPE_TARGET) == MatchResult.INTER

    def test_rope_in_center_no_winner(self) -> None:
        assert check_win(0.0, ROPE_TARGET) is None

    def test_rope_positive_not_at_target(self) -> None:
        assert check_win(50.0, ROPE_TARGET) is None

    def test_rope_negative_not_at_target(self) -> None:
        assert check_win(-50.0, ROPE_TARGET) is None

    def test_rope_just_below_positive_target_no_winner(self) -> None:
        assert check_win(99.9, ROPE_TARGET) is None

    def test_rope_just_above_negative_target_no_winner(self) -> None:
        assert check_win(-99.9, ROPE_TARGET) is None

    def test_float_boundary_inclusive_gremio(self) -> None:
        """Boundary must be inclusive: rope==100.0 (float) → GREMIO."""
        assert check_win(100.0, ROPE_TARGET) == MatchResult.GREMIO

    def test_float_boundary_inclusive_inter(self) -> None:
        assert check_win(-100.0, ROPE_TARGET) == MatchResult.INTER


# ---------------------------------------------------------------------------
# resolve_result
# ---------------------------------------------------------------------------


class TestResolveResult:
    def test_timed_out_no_threshold_gives_draw(self) -> None:
        """timed_out=True, rope=-30 (not at threshold) → (DRAW, TIMEOUT)."""
        state = _state(-30.0)
        result, reason = resolve_result(state, timed_out=True, rope_target=ROPE_TARGET)
        assert result == MatchResult.DRAW
        assert reason == EndReason.TIMEOUT

    def test_rope_at_positive_target_not_timed_out_gremio_wins(self) -> None:
        """rope==+100, timed_out=False → (GREMIO, WIN)."""
        state = _state(float(ROPE_TARGET))
        result, reason = resolve_result(state, timed_out=False, rope_target=ROPE_TARGET)
        assert result == MatchResult.GREMIO
        assert reason == EndReason.WIN

    def test_rope_at_negative_target_not_timed_out_inter_wins(self) -> None:
        """rope==-100, timed_out=False → (INTER, WIN)."""
        state = _state(-float(ROPE_TARGET))
        result, reason = resolve_result(state, timed_out=False, rope_target=ROPE_TARGET)
        assert result == MatchResult.INTER
        assert reason == EndReason.WIN

    def test_timed_out_with_rope_at_gremio_side_gremio_wins(self) -> None:
        """When threshold IS reached and timed_out=True, the win takes priority."""
        state = _state(float(ROPE_TARGET))
        result, reason = resolve_result(state, timed_out=True, rope_target=ROPE_TARGET)
        assert result == MatchResult.GREMIO
        assert reason == EndReason.WIN

    def test_timed_out_with_rope_at_inter_side_inter_wins(self) -> None:
        """When threshold IS reached and timed_out=True, the win takes priority."""
        state = _state(-float(ROPE_TARGET))
        result, reason = resolve_result(state, timed_out=True, rope_target=ROPE_TARGET)
        assert result == MatchResult.INTER
        assert reason == EndReason.WIN

    def test_timed_out_center_rope_draw(self) -> None:
        state = _state(0.0)
        result, reason = resolve_result(state, timed_out=True, rope_target=ROPE_TARGET)
        assert result == MatchResult.DRAW
        assert reason == EndReason.TIMEOUT
