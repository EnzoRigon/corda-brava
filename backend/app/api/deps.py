"""App-scoped singletons (settings, repos, queue, registry, service) for ``Depends``.

The container is built in the app lifespan (or lazily on first use), cached on app.state.container;
tests may pre-set ``app.state.container`` or use ``app.dependency_overrides[get_container]``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from app.core.settings import Settings
from app.queue.factory import make_event_queue
from app.queue.interfaces import EventQueue
from app.repositories.sqlite.bootstrap import bootstrap_db
from app.repositories.sqlite.event_repo import SQLiteEventRepository
from app.repositories.sqlite.match_repo import SQLiteMatchRepository
from app.repositories.sqlite.player_repo import SQLitePlayerRepository
from app.services.match_service import MatchService
from app.services.registry import MatchRegistry


@dataclass
class Container:
    settings: Settings
    matches: SQLiteMatchRepository
    players: SQLitePlayerRepository
    events: SQLiteEventRepository
    queue: EventQueue
    registry: MatchRegistry
    service: MatchService
    # shortcut: per-process batchId->expiry (monotonic); swap for Redis when scaled out
    seen_batches: dict[str, float] = field(default_factory=dict)


def _db_path(settings: Settings) -> str:
    url = settings.DATABASE_URL
    return url.removeprefix("sqlite:///") if url.startswith("sqlite:///") else url


def build_container(settings: Settings) -> Container:
    db = _db_path(settings)
    bootstrap_db(db)
    matches, players, events = (
        SQLiteMatchRepository(db),
        SQLitePlayerRepository(db),
        SQLiteEventRepository(db),
    )
    queue, registry = make_event_queue(settings), MatchRegistry()
    service = MatchService(
        matches=matches,
        players=players,
        events=events,
        queue=queue,
        registry=registry,
        settings=settings,
    )
    return Container(settings, matches, players, events, queue, registry, service)


def get_container(app: FastAPI) -> Container:
    if getattr(app.state, "container", None) is None:
        app.state.container = build_container(app.state.settings)
    return app.state.container


def container_dep(request: Request) -> Container:
    """FastAPI dependency; override via ``app.dependency_overrides[container_dep]``."""
    return get_container(request.app)


ContainerDep = Annotated[Container, Depends(container_dep)]
