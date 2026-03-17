"""PDF text extraction using pypdf.

Extracts per-page text and document-level metadata from a PDF file.
Does NOT perform chunking — see chunking.py for that.

Raises PipelineError (not bare exceptions) for all failure modes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PageContent:
    """Text and metadata for a single PDF page."""

    page_number: int  # 1-based
    text: str


@dataclass(frozen=True)
class PdfDocumentContent:
    """Full extracted content of a PDF document."""

    path: Path
    pages: list[PageContent]
    title: str
    author: str
    creation_date: str
    page_count: int

    @property
    def full_text(self) -> str:
        """Concatenated text of all pages, separated by double newlines."""
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def extract_pdf(path: Path) -> PdfDocumentContent:
    """Extract text from *path* and return structured page content.

    Args:
        path: Absolute or relative path to the PDF file.

    Returns:
        PdfDocumentContent with per-page text and document metadata.

    Raises:
        PipelineError(INGEST_READ_FAILURE): File not found or cannot be parsed.
        PipelineError(INGEST_EMPTY_CONTENT): No text extracted (possibly image-only PDF).
    """
    if not path.exists():
        raise PipelineError(
            ErrorCode.INGEST_READ_FAILURE,
            f"PDF file not found: {path}",
            context={"path": str(path)},
        )

    try:
        reader = PdfReader(str(path))
    except (PdfReadError, Exception) as exc:
        raise PipelineError(
            ErrorCode.INGEST_READ_FAILURE,
            f"Cannot open PDF '{path}': {exc}",
            context={"path": str(path)},
        ) from exc

    # Extract document-level metadata (values may be None in some PDFs)
    meta = reader.metadata or {}
    title = str(meta.get("/Title", "") or "")
    author = str(meta.get("/Author", "") or "")
    creation_date = str(meta.get("/CreationDate", "") or "")

    pages: list[PageContent] = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not extract text from page %d of '%s': %s",
                page_num, path, exc,
            )
            text = ""
        pages.append(PageContent(page_number=page_num, text=text))

    total_chars = sum(len(p.text) for p in pages)
    if total_chars == 0:
        raise PipelineError(
            ErrorCode.INGEST_EMPTY_CONTENT,
            f"No text extracted from PDF (possibly image-only): {path}",
            context={"path": str(path), "page_count": str(len(pages))},
        )

    logger.info(
        "Extracted %d page(s), %d chars from '%s'",
        len(pages), total_chars, path.name,
    )
    return PdfDocumentContent(
        path=path,
        pages=pages,
        title=title,
        author=author,
        creation_date=creation_date,
        page_count=len(pages),
    )
