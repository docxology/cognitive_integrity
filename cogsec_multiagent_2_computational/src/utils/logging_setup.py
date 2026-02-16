"""Structured logging setup for the CogSec framework.

Provides a lightweight logging configuration that produces structured
output suitable for both interactive use and machine parsing.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

_CONFIGURED = False


def setup_logging(
    level: int = logging.INFO,
    *,
    fmt: Optional[str] = None,
    stream: Optional[object] = None,
) -> None:
    """Configure the root logger for the framework.

    Calling this multiple times is safe — subsequent calls are no-ops unless
    *force* behaviour is needed (clear handlers first).

    Args:
        level: Logging level (default ``INFO``).
        fmt: Custom format string.  Defaults to a structured format with
            timestamp, level, logger name, and message.
        stream: Output stream (default ``sys.stderr``).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    if fmt is None:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger("cogsec")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the ``cogsec`` namespace.

    Args:
        name: Sub-logger name (e.g. ``'trust'``, ``'evaluation.runner'``).

    Returns:
        A ``logging.Logger`` scoped to ``cogsec.<name>``.
    """
    return logging.getLogger(f"cogsec.{name}")
