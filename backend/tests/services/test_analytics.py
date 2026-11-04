from datetime import UTC, datetime, timedelta

from app.domain.entities import Match, MatchConfig, Player, PullEvent, TeamConfig
from app.domain.enums import BalanceMode, EndReason, MatchResult, MatchStatus, Team
from app.services.analytics import compute_analytics

T0 = datetime(2026, 1, 1, tzinfo=UTC)
INT, G = Team.INTER, Team.GREMIO


def _match(reason=EndReason.TIMEOUT, result=MatchResult.INTER, rope=-30.0, dur=10):
    tc = TeamConfig(id="x", name="X", primary_color="#000", secondary_color="#fff")
    return Match(
        id="M",
        status=MatchStatus.FINISHED,
        config=MatchConfig(
            duration_s=dur,
            rope_target=100,
            balance_mode=BalanceMode.NORMALIZED,
            inter=tc,
            gremio=tc,
        ),
        rope_position=rope,
        started_at=T0,
        result=result,
        end_reason=reason,
    )


def _p(pid, team, name=None):
    return Player(id=pid, match_id="M", device_id=pid, name=name or pid, team=team, token="t")


def _e(pid, team, count, sec):
    return PullEvent(
        id=f"e{pid}{sec}{count}",
        match_id="M",
        player_id=pid,
        team=team,
        count=count,
        client_ts=0,
        server_ts=T0 + timedelta(seconds=sec),
        batch_id=f"b{pid}{sec}{count}",
    )


def test_bucketing_and_peak():
    players = [_p("a", INT), _p("b", G)]
    events = [
        _e("a", INT, 3, 0.2),
        _e("a", INT, 2, 0.9),
        _e("b", G, 4, 1.5),
        _e("a", INT, 5, 3.0),
        _e("b", G, 5, 3.9),
    ]
    a = compute_analytics(_match(), players, events)
    first4 = [(p.t, p.inter, p.gremio) for p in a.pullsPerSecond[:4]]
    assert first4 == [(0, 5, 0), (1, 0, 4), (2, 0, 0), (3, 5, 5)]
    assert len(a.pullsPerSecond) == 10  # full duration on timeout
    assert a.peak.model_dump() == {"value": 10, "t": 3}
    assert a.totalPulls.model_dump() == {"overall": 19, "inter": 10, "gremio": 9}
    assert a.finalRope == -30.0 and a.result == "inter" and a.endReason == "timeout"


def test_best_worst_and_percentages():
    players = [_p("a", INT), _p("b", INT), _p("c", INT), _p("d", G)]
    events = [_e("a", INT, 6, 0), _e("b", INT, 2, 1), _e("d", G, 12, 1)]
    a = compute_analytics(_match(), players, events)
    t = a.teams.inter
    assert (t.bestPlayer.playerId, t.worstPlayer.playerId) == ("a", "c")
    assert t.avgPullsPerPlayer == round(8 / 3, 2) and t.players == 3
    pa = next(p for p in a.players if p.playerId == "a")
    assert pa.pctOfTeam == 75.0 and pa.pctOfAll == 30.0 and pa.pullsPerSec == 0.6
    assert a.teams.gremio.bestPlayer.playerId == a.teams.gremio.worstPlayer.playerId == "d"
    assert [p.playerId for p in a.leaderboard] == ["d", "a", "b", "c"]


def test_empty_events_and_empty_team():
    a = compute_analytics(_match(result=MatchResult.DRAW, rope=0), [_p("a", INT)], [])
    assert a.totalPulls.overall == 0 and a.peak.value == 0
    assert a.teams.gremio.bestPlayer is None and a.teams.gremio.avgPullsPerPlayer == 0.0
    assert a.players[0].pctOfTeam == 0.0 and a.players[0].pctOfAll == 0.0
    b = compute_analytics(_match(reason=EndReason.WIN), [], [])
    assert b.durationS == 0 and b.pullsPerSecond == [] and b.leaderboard == []


def test_win_duration_and_ties_deterministic():
    players = [_p("z", INT, "Zed"), _p("y", INT, "Amy"), _p("g", G)]
    events = [_e("z", INT, 5, 0), _e("y", INT, 5, 2.5)]
    a = compute_analytics(_match(reason=EndReason.WIN), players, events)
    assert a.durationS == 3
    assert a.teams.inter.bestPlayer.name == "Amy"  # tie -> name order
    b = compute_analytics(_match(reason=EndReason.WIN), list(reversed(players)), events)
    assert [p.playerId for p in b.players] == [p.playerId for p in a.players]
    assert len(compute_analytics(_match(), players, events, top_n=1).leaderboard) == 1
