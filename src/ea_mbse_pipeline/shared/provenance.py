"""Provenance tracking for canonical model elements.

Every ModelElement, ModelRelationship, and ModelDiagram must carry a Provenance
instance identifying where it was derived from. This satisfies the requirement
that "every derivation must have provenance".
"""

from __future__ import annotations

from pydantic import BaseModel


class SourceRef(BaseModel):
    """A single source reference within a file."""

    file_path: str
    """Absolute or repo-relative path to the source file."""
    page: int | None = None
    """PDF page number (1-based), if applicable."""
    line: int | None = None
    """Line number within a text file, if applicable."""
    region: str | None = None
    """Human-readable region description, e.g. 'Figure 3', 'Section 2.1'."""


class Provenance(BaseModel):
    """Full provenance record for a derived canonical model artefact."""

    sources: list[SourceRef]
    """All source references that contributed to this artefact."""
    derivation_method: str
    """How the artefact was derived, e.g. 'text-extraction', 'ocr', 'rule-R-001'."""
    confidence: float | None = None
    """Optional confidence score in [0.0, 1.0] for AI-derived elements."""
    notes: str = ""
