"""Pure analytics over a finished match (no IO). See prompt.md section 15."""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.entities import Match, Player, PullEvent
from app.domain.enums import EndReason, Team
from app.schemas.analytics import (
    AnalyticsPayload,
    Peak,
    PlayerStats,
    PullTotals,
    TeamCounts,
    TeamsStats,
    TeamStats,
    TimelinePoint,
)

LEADERBOARD_SIZE = 5


def _pct(part: float, whole: float) -> float:
    return round(100.0 * part / whole, 2) if whole else 0.0


def compute_analytics(
    match: Match,
    players: Sequence[Player],
    events: Sequence[PullEvent],
    top_n: int = LEADERBOARD_SIZE,
) -> AnalyticsPayload:
    per_player: dict[str, int] = {p.id: 0 for p in players}
    team_totals = {Team.INTER: 0, Team.GREMIO: 0}
    buckets: dict[int, dict[Team, int]] = {}
    for ev in events:
        per_player[ev.player_id] = per_player.get(ev.player_id, 0) + ev.count
        team_totals[ev.team] += ev.count
        if match.started_at is not None:
            sec = max(0, int((ev.server_ts - match.started_at).total_seconds()))
            b = buckets.setdefault(sec, {Team.INTER: 0, Team.GREMIO: 0})
            b[ev.team] += ev.count
    total = sum(team_totals.values())

    # Duration actually played: full length on timeout, else up to the last pull.
    cfg = match.config.duration_s
    if match.end_reason == EndReason.TIMEOUT:
        duration = cfg
    else:
        duration = min(cfg, max(buckets, default=-1) + 1)

    size = max(duration, max(buckets, default=-1) + 1)
    timeline = [
        TimelinePoint(
            t=t,
            inter=buckets.get(t, {}).get(Team.INTER, 0),
            gremio=buckets.get(t, {}).get(Team.GREMIO, 0),
        )
        for t in range(size)
    ]
    # Ties resolve to the earliest second.
    top = max(timeline, key=lambda p: (p.inter + p.gremio, -p.t), default=None)
    peak = Peak(value=top.inter + top.gremio, t=top.t) if top else Peak(value=0, t=0)

    def stats(p: Player) -> PlayerStats:
        n = per_player[p.id]
        return PlayerStats(
            playerId=p.id,
            name=p.name,
            team=p.team.value,
            pulls=n,
            pctOfTeam=_pct(n, team_totals[p.team]),
            pctOfAll=_pct(n, total),
            pullsPerSec=round(n / duration, 2) if duration else 0.0,
        )

    # Deterministic order: most pulls first, then name, then id.
    all_stats = sorted((stats(p) for p in players), key=lambda s: (-s.pulls, s.name, s.playerId))

    def team_stats(team: Team) -> TeamStats:
        mine = [s for s in all_stats if s.team == team.value]
        return TeamStats(
            players=len(mine),
            totalPulls=team_totals[team],
            avgPullsPerPlayer=round(team_totals[team] / len(mine), 2) if mine else 0.0,
            bestPlayer=mine[0] if mine else None,
            worstPlayer=(min(mine, key=lambda s: (s.pulls, s.name, s.playerId)) if mine else None),
        )

    return AnalyticsPayload(
        result=match.result.value if match.result else None,
        endReason=match.end_reason.value if match.end_reason else None,
        durationS=duration,
        totalPlayers=len(players),
        playersPerTeam=TeamCounts(
            inter=sum(p.team == Team.INTER for p in players),
            gremio=sum(p.team == Team.GREMIO for p in players),
        ),
        totalPulls=PullTotals(
            overall=total, inter=team_totals[Team.INTER], gremio=team_totals[Team.GREMIO]
        ),
        pullsPerSecond=timeline,
        peak=peak,
        finalRope=match.rope_position,
        teams=TeamsStats(inter=team_stats(Team.INTER), gremio=team_stats(Team.GREMIO)),
        players=all_stats,
        leaderboard=all_stats[:top_n],
    )
