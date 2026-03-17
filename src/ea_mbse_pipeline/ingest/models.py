"""Ingestion output models.

Stage 1 data contracts:
  RawContent        — single-file ingestor output (used by IngestorProtocol)
  SourceDocument    — file-level record for a corpus document
  CorpusChunk       — a text excerpt ready for retrieval indexing
  ImageAsset        — a discovered or extracted image file
  IngestRunManifest — full output of an IngestPipeline run
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from ea_mbse_pipeline.shared.provenance import SourceRef


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Single-file ingestor contract (used by IngestorProtocol / BaseIngestor)
# ---------------------------------------------------------------------------


class InputKind(StrEnum):
    TEXT = "text"
    IMAGE = "image"  # screenshots, diagrams — supporting only
    PDF = "pdf"
    UNKNOWN = "unknown"


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


# ---------------------------------------------------------------------------
# Directory-level ingest storage models
# ---------------------------------------------------------------------------


class SourceDocument(BaseModel):
    """Metadata record for a single ingested source file."""

    doc_id: str
    """Deterministic identifier derived from file name and size."""
    file_path: str
    """Absolute or repo-relative path to the source file."""
    file_name: str
    """Base file name without directory component."""
    source_type: InputKind
    file_size_bytes: int
    page_count: int | None = None
    """Number of pages (PDF only)."""
    char_count: int | None = None
    """Total character count of extracted text."""
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, str] = {}
    """Format-specific metadata: title, author, creation date, …"""


class CorpusChunk(BaseModel):
    """A text excerpt from a source document, ready for retrieval indexing.

    Every CorpusChunk carries ``provenance_sources`` so that downstream stages
    (retrieval, canonical builder) can trace each chunk back to its origin
    without re-reading the source file.
    """

    chunk_id: str
    """UUID for this chunk."""
    doc_id: str
    """FK → SourceDocument.doc_id."""
    source_file: str
    """Absolute or repo-relative path to the originating file."""
    source_type: InputKind
    page_start: int | None = None
    """First page of this chunk (1-based, PDF only)."""
    page_end: int | None = None
    """Last page of this chunk (1-based, PDF only)."""
    section_title: str | None = None
    """Detected heading / section that this chunk belongs to."""
    text: str
    """Normalised text content."""
    char_count: int = 0
    detected_keywords: list[str] = []
    created_at: datetime = Field(default_factory=_utcnow)
    object_type: str | None = None
    """Optional EA element type hint (e.g. 'Component', 'Actor')."""
    discipline: str | None = None
    """Optional domain discipline (e.g. 'Architecture', 'Security')."""
    provenance_sources: list[SourceRef] = []
    """Source references for downstream provenance tracking."""


class ImageAsset(BaseModel):
    """A discovered or extracted image file (screenshot, diagram)."""

    asset_id: str
    file_path: str
    """Absolute path to the image file."""
    source_doc_id: str | None = None
    """doc_id of the PDF this was extracted from, if applicable."""
    page: int | None = None
    """PDF page (1-based) this was extracted from, if applicable."""
    width_px: int | None = None
    height_px: int | None = None
    format: str | None = None
    """Image format string, e.g. 'PNG', 'JPEG'."""
    description: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


class IngestRunManifest(BaseModel):
    """Full output record of a single IngestPipeline run.

    Written to ``output_dir/{run_id}/manifest.json`` and
    ``output_dir/{run_id}/ingest.db`` after every pipeline run.
    """

    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    corpus_dir: str
    metamodel_dir: str
    screenshots_dir: str
    source_documents: list[SourceDocument] = []
    chunks: list[CorpusChunk] = []
    image_assets: list[ImageAsset] = []
    xmi_files: list[str] = []
    """Paths to discovered XMI metamodel files (not ingested — passed to MetamodelCompiler)."""
    output_json_path: str | None = None
    output_sqlite_path: str | None = None
    errors: list[str] = []
    warnings: list[str] = []

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def document_count(self) -> int:
        return len(self.source_documents)
