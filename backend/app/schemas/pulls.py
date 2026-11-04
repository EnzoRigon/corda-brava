"""Pull ingest + /me models (camelCase JSON on the wire)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.domain.enums import MatchStatus, Team

Id = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class PullRequest(BaseModel):
    playerId: Id  # noqa: N815
    playerToken: str  # noqa: N815
    count: int  # <=0 -> 422 (handled in route); > MAX is clamped, not rejected
    clientTs: float  # noqa: N815
    batchId: Id  # noqa: N815


class PullAccepted(BaseModel):
    accepted: int  # clamped count that was (or, for a duplicate, had been) queued


class MeResponse(BaseModel):
    screen: Literal["wait", "play", "end"]
    team: Team
    matchStatus: MatchStatus  # noqa: N815
    result: Literal["INTER", "GREMIO", "DRAW"] | None = None
