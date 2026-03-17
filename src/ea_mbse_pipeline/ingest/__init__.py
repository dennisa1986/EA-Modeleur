"""Stage 1 — Ingestion.

Reads raw input files (plain text, images/screenshots, PDFs) and produces
normalised output objects.  Downstream stages must not consume raw files
directly; they consume RawContent (single-file) or load CorpusChunk records
from the IngestRunManifest produced by IngestPipeline.

Public API
----------
Single-file ingestor (IngestorProtocol contract):

    from ea_mbse_pipeline.ingest import build_ingestor
    ingestor = build_ingestor()
    raw = ingestor.ingest(Path("data/raw/corpus/my_doc.pdf"))

Directory-level pipeline (full ingest stage):

    from ea_mbse_pipeline.ingest import IngestPipeline
    manifest = IngestPipeline(
        corpus_dir=Path("data/raw/corpus"),
        metamodel_dir=Path("data/raw/metamodel"),
        screenshots_dir=Path("data/raw/screenshots"),
        output_dir=Path("data/processed/ingest"),
    ).run()
"""

from ea_mbse_pipeline.ingest.models import (
    CorpusChunk,
    ImageAsset,
    IngestRunManifest,
    InputKind,
    RawContent,
    SourceDocument,
)
from ea_mbse_pipeline.ingest.pipeline import (
    DispatchIngestor,
    ImageIngestor,
    IngestPipeline,
    PdfIngestor,
    TextIngestor,
    build_ingestor,
)

__all__ = [
    "build_ingestor",
    "CorpusChunk",
    "DispatchIngestor",
    "ImageAsset",
    "ImageIngestor",
    "IngestPipeline",
    "IngestRunManifest",
    "InputKind",
    "PdfIngestor",
    "RawContent",
    "SourceDocument",
    "TextIngestor",
]
