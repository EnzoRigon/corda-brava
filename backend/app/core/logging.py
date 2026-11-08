"""Structured logging configuration for Corda Brava.

Configures the standard ``logging`` module with a JSON-friendly format for
production and a human-friendly format for development.  Call
``configure_logging()`` once at startup (from ``create_app``).
"""

from __future__ import annotations

import logging
import sys

_HUMAN_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.INFO, *, structured: bool = False) -> None:
    """Set up root-logger handlers.

    Args:
        level: Logging level (default INFO).
        structured: When True emit a JSON-style message per record (suitable
            for log aggregators).  When False use the human-readable format.
    """
    handler = logging.StreamHandler(sys.stdout)

    if structured:
        # Minimal structured format — a full JSON formatter can replace this
        # later without touching any call-site.
        formatter = logging.Formatter(
            fmt='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
            '"line":%(lineno)d,"msg":%(message)r}',
            datefmt=_DATE_FORMAT,
        )
    else:
        formatter = logging.Formatter(fmt=_HUMAN_FORMAT, datefmt=_DATE_FORMAT)

    handler.setFormatter(formatter)

    root = logging.getLogger()
    # Remove any existing handlers to avoid duplicate output when the module
    # is imported more than once (e.g., during testing with importlib reload).
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quieten noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)  # AMQP link state changes at INFO
