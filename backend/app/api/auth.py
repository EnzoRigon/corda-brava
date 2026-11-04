"""Auth dependencies for host-only routes and WebSocket token checks."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from app.api.deps import ContainerDep
from app.core.settings import Settings
from app.services.host_session import verify_host_token


def verify_ws_token(token: str | None, settings: Settings) -> bool:
    """Check a WebSocket query-string token."""
    return bool(token) and verify_host_token(token, settings)


def require_host(
    c: ContainerDep,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """401 unless ``Authorization: Bearer <valid host token>`` is present."""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not verify_host_token(token, c.settings):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing host token",
            headers={"WWW-Authenticate": "Bearer"},
        )
