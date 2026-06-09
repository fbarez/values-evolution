"""Structured logging setup for genval scripts."""

from __future__ import annotations

import logging
import sys

from rich.logging import RichHandler


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a logger with rich formatting. Idempotent."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
