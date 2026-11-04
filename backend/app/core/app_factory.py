"""FastAPI application factory.

Centralises app construction so:
- Tests receive a fully-configured app without running Uvicorn.
- The ``main.py`` entry-point stays thin.
- Later tasks can extend the factory (add routers, lifespan events, middleware)
  without changing call-sites.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.player import router as player_router
from app.core.logging import configure_logging
from app.core.settings import Settings
from app.services.match_service import ConflictError, MatchNotFoundError

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    """Build and return a configured FastAPI application.

    Args:
        settings: Application settings instance (injected for testability).

    Returns:
        Fully wired FastAPI application ready to serve.
    """
    configure_logging()

    app = FastAPI(
        title="Corda Brava",
        description="Themed tug-of-war party game backend.",
        version="0.1.0",
    )

    app.state.settings = settings
    app.state.container = None  # built lazily by app.api.deps.get_container

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MatchNotFoundError)
    async def _not_found(_: Request, exc: MatchNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Partida não encontrada"})

    # ── CORS ─────────────────────────────────────────────────────────────────
    origins: list[str] = (
        ["*"]
        if settings.CORS_ORIGINS.strip() == "*"
        else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(player_router)

    # Root /api router — empty now; later tasks attach sub-routers here.
    from fastapi import APIRouter  # local import to keep top-level clean

    api_router = APIRouter(prefix="/api")
    app.include_router(api_router)

    logger.info("Application created (CORS origins: %s)", origins)
    return app
