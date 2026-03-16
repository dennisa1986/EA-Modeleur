"""Ingestion output models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class InputKind(StrEnum):
    TEXT       = "text"
    IMAGE      = "image"     # screenshots, diagrams — supporting only
    PDF        = "pdf"
    UNKNOWN    = "unknown"


class RawContent(BaseModel):
    """Normalised output of any ingestor.  The contract between Stage 1 and Stage 3."""

    source: Path
    kind: InputKind
    text: str = ""
    """Extracted or provided textual content."""
    image_paths: list[Path] = []
    """Paths to extracted/converted images (e.g. PDF pages rendered as PNG)."""
    metadata: dict[str, str] = {}
    """File-level metadata: MIME type, page count, dimensions, …"""
