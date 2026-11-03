"""Health-check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    """Return a simple liveness signal for Docker/load-balancer health checks."""
    return JSONResponse({"status": "ok"})
