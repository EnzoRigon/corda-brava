"""Host login request/response models (camelCase JSON on the wire)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HostLoginRequest(BaseModel):
    password: str


class HostLoginResponse(BaseModel):
    token: str
    expiresAt: datetime  # noqa: N815 - wire format is camelCase per spec
