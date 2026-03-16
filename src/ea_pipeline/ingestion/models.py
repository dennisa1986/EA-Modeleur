"""Data models for raw ingestion output."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class InputKind(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    UNKNOWN = "unknown"


class RawContent(BaseModel):
    """Normalised output of any ingestor — the contract between Stage 1 and Stage 3."""

    source: Path
    kind: InputKind
    text: str = ""
    """Extracted or provided textual content."""
    metadata: dict[str, str] = {}
    """File-level metadata (MIME type, page count, dimensions, …)."""
