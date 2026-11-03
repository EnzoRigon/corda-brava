"""Domain enumerations for Corda Brava.

All enums are str-valued so they serialize/deserialize cleanly from JSON
and SQLite text columns without extra mapping.
"""

from enum import StrEnum


class MatchStatus(StrEnum):
    """Lifecycle state of a match."""

    LOBBY = "lobby"
    RUNNING = "running"
    FINISHED = "finished"


class Team(StrEnum):
    """The two competing teams."""

    INTER = "inter"
    GREMIO = "gremio"


class MatchResult(StrEnum):
    """Who won, or draw."""

    INTER = "inter"
    GREMIO = "gremio"
    DRAW = "draw"


class EndReason(StrEnum):
    """How the match ended."""

    WIN = "win"
    TIMEOUT = "timeout"


class BalanceMode(StrEnum):
    """Rope-scoring mode."""

    RAW = "raw"
    NORMALIZED = "normalized"


class QueueBackend(StrEnum):
    """Event-queue implementation backend."""

    MEMORY = "memory"
    AZURE_SERVICE_BUS = "azure_service_bus"
