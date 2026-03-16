"""Retrieval stage output models."""

from __future__ import annotations

from pydantic import BaseModel

from ea_mbse_pipeline.shared.provenance import SourceRef


class RetrievedChunk(BaseModel):
    """A single retrieved text or image chunk from the corpus."""

    chunk_id: str
    text: str
    source: SourceRef
    score: float
    """Relevance score in [0.0, 1.0]."""


class RetrievalResult(BaseModel):
    """Aggregated retrieval result for a single query."""

    query: str
    chunks: list[RetrievedChunk] = []
