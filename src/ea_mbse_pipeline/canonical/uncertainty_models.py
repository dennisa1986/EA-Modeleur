"""Uncertainty models for the canonical layer.

When the pipeline derives elements with low confidence — due to ambiguous
source text, poor OCR quality, or conflicting evidence — it records an
``Uncertainty`` entry on the ``CanonicalModel``.

Downstream stages (Validator, Serializer) can choose to:
- reject elements above a configurable uncertainty threshold,
- surface uncertainties to the operator in a review report, or
- pass them through with a warning annotation in the XMI output.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class UncertaintyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UncertaintyType(StrEnum):
    EXTRACTION = "extraction"
    """Uncertain what was extracted from the source (e.g. poor OCR quality)."""
    CLASSIFICATION = "classification"
    """Uncertain which ElementKind or RelationshipKind applies."""
    RELATIONSHIP = "relationship"
    """Uncertain whether a relationship exists or what its direction is."""
    PROVENANCE = "provenance"
    """Uncertain which source document / chunk the element came from."""
    COMPLETENESS = "completeness"
    """Model may be structurally incomplete (e.g. missing attributes)."""


class Uncertainty(BaseModel):
    """Records an identified uncertainty in a canonical artefact."""

    id: str = Field(..., description="Pipeline-internal UUID for this uncertainty record.")
    element_id: str = Field(
        ...,
        description="ID of the canonical artefact this uncertainty pertains to.",
    )
    uncertainty_type: UncertaintyType
    level: UncertaintyLevel
    description: str = Field(..., description="Human-readable description of the uncertainty.")
    mitigation: str = Field(
        default="",
        description="Optional suggestion for how to resolve this uncertainty.",
    )
