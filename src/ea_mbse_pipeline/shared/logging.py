"""Structured logging configuration for the MBSE pipeline.

Usage in any module:
    from ea_mbse_pipeline.shared.logging import get_logger
    logger = get_logger(__name__)
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with a structured format.

    Call once at application startup (e.g. from cli.py or orchestration).
    """
    logging.basicConfig(
        stream=sys.stderr,
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.  Always prefer this over logging.getLogger directly."""
    return logging.getLogger(name)
