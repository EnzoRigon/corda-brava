"""Host routes: login, match lifecycle, analytics. All but login require a host token."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import require_host
from app.api.deps import Container, ContainerDep
from app.domain.entities import Match
from app.domain.enums import MatchStatus, Team
from app.schemas.analytics import AnalyticsPayload
from app.schemas.host import HostLoginRequest, HostLoginResponse
from app.schemas.match import (
    ConfigOut,
    CreateMatchRequest,
    CreateMatchResponse,
    MatchView,
    Roster,
    RosterPlayer,
    Scores,
    TeamScore,
    UpdateMatchRequest,
    config_out,
)
from app.services.analytics import compute_analytics
from app.services.host_session import check_password, issue_host_token
from app.services.match_service import MatchNotFoundError

router = APIRouter(prefix="/api/host", tags=["host"])
protected = APIRouter(prefix="/api/host", tags=["host"], dependencies=[Depends(require_host)])

BAD_PASSWORD = "Senha incorreta"
BAD_DURATION = "Duração fora do intervalo permitido"


def match_view(c: Container, match_id: str) -> MatchView:
    state = c.service.get_match_view(match_id)
    m = c.matches.get_match(match_id)
    players = c.players.list_players(match_id)
    pulls = {Team.INTER: 0, Team.GREMIO: 0}
    for e in c.events.list_events(match_id):
        pulls[e.team] += e.count
    return MatchView(
        id=m.id,
        status=state.status.value.upper(),
        config=config_out(m.config),
        roster=Roster(
            **{
                t.value: [RosterPlayer(id=p.id, name=p.name) for p in players if p.team is t]
                for t in Team
            }
        ),
        rope=state.rope_position,
        remainingS=state.remaining_s or 0.0,
        scores=Scores(
            inter=TeamScore(pulls=pulls[Team.INTER]), gremio=TeamScore(pulls=pulls[Team.GREMIO])
        ),
        result=state.result.value.upper() if state.result else None,
        endReason=state.end_reason.value if state.end_reason else None,
    )


def _created(c: Container, m: Match) -> CreateMatchResponse:
    url = f"{c.settings.PUBLIC_BASE_URL.rstrip('/')}/j/{m.id}"
    return CreateMatchResponse(
        matchId=m.id, joinUrl=url, qrPayload=url, config=config_out(m.config)
    )


@router.post("/login", response_model=HostLoginResponse)
def login(body: HostLoginRequest, c: ContainerDep) -> HostLoginResponse:
    if not check_password(body.password, c.settings):
        raise HTTPException(status_code=401, detail=BAD_PASSWORD)
    token, expires_at = issue_host_token(c.settings)
    return HostLoginResponse(token=token, expiresAt=expires_at)


@protected.post("/matches", response_model=CreateMatchResponse, status_code=201)
def create_match(body: CreateMatchRequest, c: ContainerDep) -> CreateMatchResponse:
    try:
        m = c.service.create_match(body.durationS, body.balanceMode)
    except ValueError:
        raise HTTPException(status_code=422, detail=BAD_DURATION) from None
    return _created(c, m)


@protected.get("/matches/{match_id}", response_model=MatchView)
def get_match(match_id: str, c: ContainerDep) -> MatchView:
    return match_view(c, match_id)


@protected.patch("/matches/{match_id}", response_model=ConfigOut)
def update_match(match_id: str, body: UpdateMatchRequest, c: ContainerDep) -> ConfigOut:
    try:
        return config_out(c.service.update_duration(match_id, body.durationS).config)
    except ValueError:
        raise HTTPException(status_code=422, detail=BAD_DURATION) from None


@protected.post("/matches/{match_id}/start", response_model=MatchView)
async def start_match(match_id: str, c: ContainerDep) -> MatchView:
    c.service.start(match_id)  # async route: the consumer task needs the running loop
    return match_view(c, match_id)


@protected.post("/matches/{match_id}/cancel", response_model=MatchView)
async def cancel_match(match_id: str, c: ContainerDep) -> MatchView:
    if c.matches.get_match(match_id) is None:
        raise MatchNotFoundError(match_id)
    # service.cancel() clears the WS listeners, so tell them first.
    await c.registry.broadcast(match_id, {"type": "cancelled"})
    await c.service.cancel(match_id)
    return match_view(c, match_id)


@protected.post("/matches/{match_id}/reset", response_model=CreateMatchResponse, status_code=201)
async def reset_match(match_id: str, c: ContainerDep) -> CreateMatchResponse:
    """Cancel the match and create a fresh LOBBY match with the same duration/balance mode."""
    old = c.matches.get_match(match_id)
    if old is None:
        raise MatchNotFoundError(match_id)
    new = c.service.create_match(old.config.duration_s, old.config.balance_mode)
    await c.registry.broadcast(match_id, {"type": "reset", "newMatchId": new.id})
    await c.service.cancel(match_id)
    return _created(c, new)


@protected.get("/matches/{match_id}/analytics", response_model=AnalyticsPayload)
def analytics(match_id: str, c: ContainerDep) -> AnalyticsPayload:
    m = c.matches.get_match(match_id)
    if m is None:
        raise MatchNotFoundError(match_id)
    if m.status is not MatchStatus.FINISHED:
        raise HTTPException(status_code=409, detail="A partida ainda não terminou")
    return compute_analytics(m, c.players.list_players(match_id), c.events.list_events(match_id))
