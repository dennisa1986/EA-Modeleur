"""Ingest pipeline stage and concrete ingestor implementations.

Exports:
  PdfIngestor      — ingest a single PDF file → RawContent
  TextIngestor     — ingest a single text file → RawContent
  ImageIngestor    — ingest a single image file → RawContent (supporting only)
  DispatchIngestor — dispatches to the correct ingestor by file extension
  build_ingestor() — factory that returns a DispatchIngestor

  IngestPipeline   — high-level runner: discovers directories, extracts text,
                     chunks, and persists to JSON + SQLite.

Source directories consumed by IngestPipeline.run():
  corpus_dir      PDF and text files → SourceDocument + CorpusChunk records
  metamodel_dir   XMI/XML files      → listed in manifest.xmi_files only
  screenshots_dir Image files        → ImageAsset records

Output written by IngestPipeline.run():
  output_dir/{run_id}/manifest.json  — full IngestRunManifest
  output_dir/{run_id}/chunks.json    — CorpusChunk list (retrieval-ready)
  output_dir/{run_id}/ingest.db      — SQLite database
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ea_mbse_pipeline.ingest.chunking import chunk_pdf_pages, chunk_text
from ea_mbse_pipeline.ingest.file_discovery import (
    discover_corpus_files,
    discover_metamodel_files,
    ensure_directory,
)
from ea_mbse_pipeline.ingest.image_manifest import build_image_manifest
from ea_mbse_pipeline.ingest.metadata import (
    build_corpus_chunk,
    build_source_document,
    doc_id_from_path,
)
from ea_mbse_pipeline.ingest.models import (
    CorpusChunk,
    IngestRunManifest,
    InputKind,
    RawContent,
    SourceDocument,
)
from ea_mbse_pipeline.ingest.pdf_extract import extract_pdf
from ea_mbse_pipeline.ingest.protocols import BaseIngestor
from ea_mbse_pipeline.ingest.store_json import save_chunks_json, save_manifest_json
from ea_mbse_pipeline.ingest.store_sqlite import save_to_sqlite
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)

_TEXT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".rst", ".text"})
_PDF_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
_IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp",
})


# ---------------------------------------------------------------------------
# Concrete single-file ingestor implementations
# ---------------------------------------------------------------------------

class PdfIngestor(BaseIngestor):
    """Ingest a single PDF file and return a RawContent with full extracted text."""

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in _PDF_EXTENSIONS

    def ingest(self, source: Path) -> RawContent:
        doc = extract_pdf(source)
        return RawContent(
            source=source,
            kind=InputKind.PDF,
            text=doc.full_text,
            metadata={
                "page_count": str(doc.page_count),
                "title": doc.title,
                "author": doc.author,
                "creation_date": doc.creation_date,
            },
        )


class TextIngestor(BaseIngestor):
    """Ingest a plain-text file (.txt, .md, .rst) and return a RawContent."""

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in _TEXT_EXTENSIONS

    def ingest(self, source: Path) -> RawContent:
        if not source.exists():
            raise PipelineError(
                ErrorCode.INGEST_READ_FAILURE,
                f"Text file not found: {source}",
                context={"path": str(source)},
            )
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise PipelineError(
                ErrorCode.INGEST_READ_FAILURE,
                f"Cannot read text file '{source}': {exc}",
                context={"path": str(source)},
            ) from exc
        if not text.strip():
            raise PipelineError(
                ErrorCode.INGEST_EMPTY_CONTENT,
                f"Text file is empty: {source}",
                context={"path": str(source)},
            )
        return RawContent(
            source=source,
            kind=InputKind.TEXT,
            text=text,
            metadata={"char_count": str(len(text))},
        )


class ImageIngestor(BaseIngestor):
    """Ingest an image file — supporting only, no text extraction."""

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in _IMAGE_EXTENSIONS

    def ingest(self, source: Path) -> RawContent:
        if not source.exists():
            raise PipelineError(
                ErrorCode.INGEST_READ_FAILURE,
                f"Image file not found: {source}",
                context={"path": str(source)},
            )
        return RawContent(
            source=source,
            kind=InputKind.IMAGE,
            text="",
            image_paths=[source],
            metadata={"format": source.suffix.lstrip(".").upper()},
        )


class DispatchIngestor(BaseIngestor):
    """Dispatches ingest calls to the appropriate implementation by file extension.

    Tries PdfIngestor, TextIngestor, and ImageIngestor in that order.
    Raises PipelineError(INGEST_UNSUPPORTED_FORMAT) if no ingestor matches.
    """

    def __init__(self) -> None:
        self._ingestors: list[BaseIngestor] = [
            PdfIngestor(),
            TextIngestor(),
            ImageIngestor(),
        ]

    def supports(self, source: Path) -> bool:
        return any(i.supports(source) for i in self._ingestors)

    def ingest(self, source: Path) -> RawContent:
        for ingestor in self._ingestors:
            if ingestor.supports(source):
                logger.debug(
                    "Dispatching '%s' to %s",
                    source.name, type(ingestor).__name__,
                )
                return ingestor.ingest(source)
        raise PipelineError(
            ErrorCode.INGEST_UNSUPPORTED_FORMAT,
            f"No ingestor available for '{source.name}' (extension: {source.suffix!r})",
            context={"path": str(source), "suffix": source.suffix},
        )


def build_ingestor() -> DispatchIngestor:
    """Factory function — returns a configured DispatchIngestor.

    Usage::

        from ea_mbse_pipeline.ingest import build_ingestor
        ingestor = build_ingestor()
        raw = ingestor.ingest(Path("data/raw/corpus/my_doc.pdf"))
    """
    return DispatchIngestor()


# ---------------------------------------------------------------------------
# High-level IngestPipeline
# ---------------------------------------------------------------------------

class IngestPipeline:
    """Full ingest stage: discovers files, extracts text, chunks, and saves outputs.

    Args:
        corpus_dir:      Directory containing PDF and text corpus documents.
        metamodel_dir:   Directory containing XMI metamodel files.
        screenshots_dir: Directory containing screenshot image files (optional).
        output_dir:      Base output directory; a sub-directory per run_id is created.
        recursive:       If ``True`` (default), all three source directories are
                         scanned recursively.  Set to ``False`` to limit discovery
                         to the top-level directory only.

    Example::

        pipeline = IngestPipeline(
            corpus_dir=Path("data/raw/corpus"),
            metamodel_dir=Path("data/raw/metamodel"),
            screenshots_dir=Path("data/raw/screenshots"),
            output_dir=Path("data/processed/ingest"),
        )
        manifest = pipeline.run()
    """

    def __init__(
        self,
        corpus_dir: Path,
        metamodel_dir: Path,
        screenshots_dir: Path,
        output_dir: Path,
        *,
        recursive: bool = True,
    ) -> None:
        self._corpus_dir = corpus_dir
        self._metamodel_dir = metamodel_dir
        self._screenshots_dir = screenshots_dir
        self._output_dir = output_dir
        self._recursive = recursive

    def run(self) -> IngestRunManifest:
        """Execute the full ingest stage and return the run manifest.

        Per-file errors are collected into ``manifest.errors`` and logged at
        ERROR level, but do not abort the run — partial ingestion is better
        than none.  An exception is raised only for storage failures.

        Returns:
            IngestRunManifest with all discovered documents, chunks, and images.

        Raises:
            PipelineError: If output files cannot be written.
        """
        run_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        logger.info("Ingest run %s starting", run_id)

        manifest = IngestRunManifest(
            run_id=run_id,
            started_at=started_at,
            corpus_dir=str(self._corpus_dir),
            metamodel_dir=str(self._metamodel_dir),
            screenshots_dir=str(self._screenshots_dir),
        )

        # 1. Metamodel discovery (XMI files listed for MetamodelCompiler, not ingested)
        xmi_files = discover_metamodel_files(
            self._metamodel_dir, recursive=self._recursive
        )
        manifest.xmi_files = [str(f) for f in xmi_files]
        logger.info("Metamodel files: %d", len(xmi_files))

        # 2. Corpus ingestion
        corpus_files = discover_corpus_files(
            self._corpus_dir, recursive=self._recursive
        )
        for file_path in corpus_files:
            try:
                doc, chunks = self._ingest_corpus_file(file_path)
                manifest.source_documents.append(doc)
                manifest.chunks.extend(chunks)
                logger.info(
                    "Ingested '%s' → %d chunk(s)",
                    file_path.name, len(chunks),
                )
            except PipelineError as exc:
                manifest.errors.append(str(exc))
                logger.error("Ingestion failed for '%s': %s", file_path.name, exc)

        if corpus_files and not manifest.source_documents:
            manifest.warnings.append(
                "All corpus files failed to ingest — check errors field."
            )
            logger.warning("All %d corpus file(s) failed to ingest", len(corpus_files))

        # 3. Screenshot manifest (ensure directory exists even if empty)
        ensure_directory(self._screenshots_dir)
        image_assets = build_image_manifest(
            self._screenshots_dir, recursive=self._recursive
        )
        manifest.image_assets.extend(image_assets)

        manifest.finished_at = datetime.now(timezone.utc)

        # 4. Persist outputs
        run_output_dir = self._output_dir / run_id
        ensure_directory(run_output_dir)
        json_path = save_manifest_json(manifest, run_output_dir / "manifest.json")
        save_chunks_json(manifest, run_output_dir / "chunks.json")
        db_path = save_to_sqlite(manifest, run_output_dir / "ingest.db")

        # Update manifest with output paths (written again below)
        manifest.output_json_path = str(json_path)
        manifest.output_sqlite_path = str(db_path)
        # Re-save with updated paths
        save_manifest_json(manifest, run_output_dir / "manifest.json")

        logger.info(
            "Ingest run %s complete — docs: %d  chunks: %d  images: %d  errors: %d",
            run_id,
            manifest.document_count,
            manifest.chunk_count,
            len(manifest.image_assets),
            len(manifest.errors),
        )
        return manifest

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ingest_corpus_file(
        self, file_path: Path
    ) -> tuple[SourceDocument, list[CorpusChunk]]:
        """Dispatch extraction and chunking for a single corpus file."""
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return self._ingest_pdf(file_path)
        if suffix in _TEXT_EXTENSIONS:
            return self._ingest_text(file_path)
        raise PipelineError(
            ErrorCode.INGEST_UNSUPPORTED_FORMAT,
            f"Unsupported corpus file type: {file_path.suffix!r}",
            context={"path": str(file_path)},
        )

    def _ingest_pdf(
        self, file_path: Path
    ) -> tuple[SourceDocument, list[CorpusChunk]]:
        pdf_content = extract_pdf(file_path)
        doc_id = doc_id_from_path(file_path)
        doc = build_source_document(
            path=file_path,
            source_type=InputKind.PDF,
            page_count=pdf_content.page_count,
            char_count=len(pdf_content.full_text),
            extra_metadata={
                "title": pdf_content.title,
                "author": pdf_content.author,
                "creation_date": pdf_content.creation_date,
            },
        )
        raw_chunks = chunk_pdf_pages(pdf_content.pages)
        chunks = [
            build_corpus_chunk(raw, doc_id, str(file_path), InputKind.PDF)
            for raw in raw_chunks
        ]
        return doc, chunks

    def _ingest_text(
        self, file_path: Path
    ) -> tuple[SourceDocument, list[CorpusChunk]]:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise PipelineError(
                ErrorCode.INGEST_READ_FAILURE,
                f"Cannot read '{file_path}': {exc}",
                context={"path": str(file_path)},
            ) from exc
        if not text.strip():
            raise PipelineError(
                ErrorCode.INGEST_EMPTY_CONTENT,
                f"Empty file: {file_path}",
                context={"path": str(file_path)},
            )
        doc_id = doc_id_from_path(file_path)
        doc = build_source_document(
            path=file_path,
            source_type=InputKind.TEXT,
            char_count=len(text),
        )
        raw_chunks = chunk_text(text, source_name=file_path.name)
        chunks = [
            build_corpus_chunk(raw, doc_id, str(file_path), InputKind.TEXT)
            for raw in raw_chunks
        ]
        return doc, chunks
