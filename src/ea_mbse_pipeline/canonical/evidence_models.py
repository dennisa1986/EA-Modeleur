"""Evidence link models for the canonical layer.

An ``EvidenceLink`` records which chunk of a source document supports a
specific canonical model artefact.  Required for traceability — every
AI-derived element should be backed by at least one ``EvidenceLink``.

``element_id`` may reference any canonical artefact that carries an ``id``
field: ``ModelElement``, ``Package``, ``ModelRelationship``, or
``ModelDiagram``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ea_mbse_pipeline.shared.provenance import Provenance


class EvidenceLink(BaseModel):
    """A link between a canonical artefact and supporting source evidence."""

    id: str = Field(..., description="Pipeline-internal UUID for this evidence link.")
    element_id: str = Field(
        ...,
        description="ID of the canonical artefact this evidence supports.",
    )
    provenance: Provenance = Field(
        ...,
        description="Where the evidence was found (file, page, region, excerpt, etc.).",
    )
    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Retrieval relevance score in [0.0, 1.0], if available.",
    )
    excerpt: str = Field(
        default="",
        description="Short verbatim excerpt from the source document.",
    )
