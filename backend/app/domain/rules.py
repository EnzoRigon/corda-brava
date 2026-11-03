"""Pure game rules for Corda Brava.

This module is IO-free and framework-free.  It contains only the math that
drives the tug-of-war mechanic so it can be unit-tested in complete isolation.

Convention (project-wide, fixed):
    rope ∈ [-rope_target, +rope_target]
    0 = center
    negative = Inter's side (left)
    positive = Grêmio's side (right)
    rope >= +rope_target → Grêmio wins
    rope <= -rope_target → Inter wins
"""

from app.domain.entities import MatchState, TickInput
from app.domain.enums import BalanceMode, EndReason, MatchResult


def clamp(x: float, lo: float, hi: float) -> float:
    """Return x clamped to the closed interval [lo, hi]."""
    return max(lo, min(hi, x))


def apply_pulls(
    state: MatchState,
    tick: TickInput,
    *,
    balance_mode: BalanceMode,
    pull_unit: float,
    rope_target: int,
) -> MatchState:
    """Apply one consumer-tick's pull totals and return a *new* MatchState.

    The input ``state`` is never mutated.  The only field that changes is
    ``rope_position``; all other fields are copied verbatim.

    Scoring modes (``balance_mode``):
    - ``RAW``: rope_delta = (pulls_gremio - pulls_inter) * pull_unit
    - ``NORMALIZED`` (default): each team's effort is normalized by its active
      player count so that a smaller, more active team can beat a larger but
      lazier one::

          effort_team = (pulls_team / max(player_count_team, 1)) * pull_unit
          rope_delta  = effort_gremio - effort_inter

    The result is clamped to [-rope_target, +rope_target].
    """
    if balance_mode is BalanceMode.RAW:
        rope_delta = (tick.pulls_gremio - tick.pulls_inter) * pull_unit
    else:  # NORMALIZED
        effort_inter = (tick.pulls_inter / max(tick.players_inter, 1)) * pull_unit
        effort_gremio = (tick.pulls_gremio / max(tick.players_gremio, 1)) * pull_unit
        rope_delta = effort_gremio - effort_inter

    new_rope = clamp(
        state.rope_position + rope_delta,
        -float(rope_target),
        float(rope_target),
    )
    return state.model_copy(update={"rope_position": new_rope})


def check_win(rope: float, rope_target: int) -> MatchResult | None:
    """Return the winning team if a threshold has been crossed, else None.

    Boundary is *inclusive* on both sides:
    - rope >= +rope_target → Grêmio wins
    - rope <= -rope_target → Inter wins
    """
    if rope >= rope_target:
        return MatchResult.GREMIO
    if rope <= -rope_target:
        return MatchResult.INTER
    return None


def resolve_result(
    state: MatchState,
    *,
    timed_out: bool,
    rope_target: int,
) -> tuple[MatchResult, EndReason]:
    """Determine the final match result and end reason.

    Logic:
    1. Check whether a win threshold was reached (takes priority over timeout).
    2. If timed out and no threshold was crossed → DRAW / TIMEOUT.

    There is no tiebreak: a true draw is returned when the timer expires
    without either side reaching their threshold.
    """
    winner = check_win(state.rope_position, rope_target)
    if winner is not None:
        return winner, EndReason.WIN

    # If we are here, no threshold was crossed.
    # A timed-out match without a threshold crossing is a draw.
    return MatchResult.DRAW, EndReason.TIMEOUT
