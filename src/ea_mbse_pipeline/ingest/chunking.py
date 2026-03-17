"""Text chunking strategies for corpus documents.

Provides two entry points:
  chunk_pdf_pages(pages)  — chunk PDF PageContent list by detected headings
  chunk_text(text)        — chunk plain text by paragraph / heading boundaries

Both return a list of RawChunk dataclasses.  Metadata attachment happens in
metadata.py; this module is responsible only for splitting text.

Chunking strategy:
  1. Detect section headings heuristically (numbered sections, ALL CAPS, title-case lines).
  2. Start a new chunk at each heading.
  3. If a chunk exceeds _MAX_CHUNK_CHARS, split it at paragraph or sentence boundaries.
  4. Discard candidate text shorter than _MIN_CHUNK_CHARS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ea_mbse_pipeline.ingest.pdf_extract import PageContent
from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)

# Tunable thresholds
_MIN_CHUNK_CHARS: int = 80
_MAX_CHUNK_CHARS: int = 4_000

# Matches numbered sections: "1 Title", "1. Title", "1.2 Title", "1.2. Title"
_NUMBERED_SECTION_RE = re.compile(r"^\d+(\.\d+)*\.?\s+\S")


@dataclass
class RawChunk:
    """A text excerpt before metadata is attached."""

    text: str
    page_start: int | None
    page_end: int | None
    section_title: str | None


# ---------------------------------------------------------------------------
# Heading detection
# ---------------------------------------------------------------------------

def _is_heading(line: str) -> bool:
    """Heuristic: return True if *line* looks like a section heading.

    Rules (applied in order):
    - Empty or very long lines → False.
    - Matches numbered section pattern (e.g. "2.1 Overview") → True.
    - ALL CAPS line of 3+ chars → True.
    - Title-case short line that doesn't end with sentence punctuation → True.
    """
    line = line.strip()
    if not line or len(line) > 120:
        return False
    if _NUMBERED_SECTION_RE.match(line):
        return True
    if line.isupper() and len(line) >= 3:
        return True
    words = line.split()
    if (
        len(words) >= 2
        and line[-1] not in ".,:;?"
        and sum(1 for w in words if w and w[0].isupper()) >= len(words) * 0.6
        and len(line) <= 80
    ):
        return True
    return False


# ---------------------------------------------------------------------------
# PDF chunking
# ---------------------------------------------------------------------------

def chunk_pdf_pages(
    pages: list[PageContent],
    min_chars: int = _MIN_CHUNK_CHARS,
    max_chars: int = _MAX_CHUNK_CHARS,
) -> list[RawChunk]:
    """Split PDF pages into chunks by detecting section headings.

    Each heading starts a new chunk.  Pages without headings are kept as a
    single chunk (subject to *max_chars* splitting).

    Args:
        pages:     List of PageContent from pdf_extract.extract_pdf().
        min_chars: Discard chunks shorter than this.
        max_chars: Split chunks longer than this.

    Returns:
        List of RawChunk instances.
    """
    chunks: list[RawChunk] = []
    current_title: str | None = None
    current_lines: list[str] = []
    current_page_start: int | None = None
    current_page_end: int | None = None

    for page in pages:
        for line in page.text.splitlines():
            stripped = line.strip()
            if not stripped:
                current_lines.append("")
                continue

            if _is_heading(stripped):
                # Flush the accumulated text as a chunk
                candidate = "\n".join(current_lines).strip()
                if len(candidate) >= min_chars:
                    chunks.extend(
                        _split_oversized(
                            candidate, current_page_start, current_page_end,
                            current_title, max_chars,
                        )
                    )
                # Start new chunk under this heading
                current_title = stripped
                current_lines = []
                current_page_start = page.page_number
                current_page_end = page.page_number
            else:
                if current_page_start is None:
                    current_page_start = page.page_number
                current_page_end = page.page_number
                current_lines.append(line)

    # Flush final accumulation
    candidate = "\n".join(current_lines).strip()
    if len(candidate) >= min_chars:
        chunks.extend(
            _split_oversized(
                candidate, current_page_start, current_page_end,
                current_title, max_chars,
            )
        )

    logger.debug("PDF chunking produced %d chunk(s)", len(chunks))
    return chunks


# ---------------------------------------------------------------------------
# Plain-text chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    source_name: str = "",
    min_chars: int = _MIN_CHUNK_CHARS,
    max_chars: int = _MAX_CHUNK_CHARS,
) -> list[RawChunk]:
    """Split plain text by paragraph boundaries (blank lines) and headings.

    Args:
        text:        Full document text.
        source_name: Used only for debug logging.
        min_chars:   Discard chunks shorter than this.
        max_chars:   Split chunks longer than this.

    Returns:
        List of RawChunk instances (page_start/page_end always None for text files).
    """
    # Split on two or more consecutive newlines (paragraph boundaries)
    raw_paragraphs = re.split(r"\n{2,}", text)
    chunks: list[RawChunk] = []
    current_title: str | None = None
    current_parts: list[str] = []

    for para in raw_paragraphs:
        stripped = para.strip()
        if not stripped:
            continue
        first_line = stripped.splitlines()[0].strip()

        if _is_heading(first_line):
            # Flush current accumulation
            candidate = "\n\n".join(current_parts).strip()
            if len(candidate) >= min_chars:
                chunks.extend(
                    _split_oversized(candidate, None, None, current_title, max_chars)
                )
            current_title = first_line
            rest = "\n".join(stripped.splitlines()[1:]).strip()
            current_parts = [rest] if rest else []
        else:
            current_parts.append(stripped)

    # Flush final accumulation
    candidate = "\n\n".join(current_parts).strip()
    if len(candidate) >= min_chars:
        chunks.extend(
            _split_oversized(candidate, None, None, current_title, max_chars)
        )

    # Fallback: treat whole text as one chunk if no paragraph boundaries found
    if not chunks and len(text.strip()) >= min_chars:
        chunks.extend(_split_oversized(text.strip(), None, None, None, max_chars))

    logger.debug("Text chunking of '%s' produced %d chunk(s)", source_name, len(chunks))
    return chunks


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_oversized(
    text: str,
    page_start: int | None,
    page_end: int | None,
    section_title: str | None,
    max_chars: int,
) -> list[RawChunk]:
    """If *text* exceeds *max_chars*, split it at natural boundaries."""
    if len(text) <= max_chars:
        return [
            RawChunk(
                text=text,
                page_start=page_start,
                page_end=page_end,
                section_title=section_title,
            )
        ]

    parts: list[RawChunk] = []
    while len(text) > max_chars:
        slice_text = text[:max_chars]
        # Prefer paragraph break, then sentence break, then hard cut
        break_at = slice_text.rfind("\n\n")
        if break_at < max_chars // 2:
            break_at = slice_text.rfind(". ")
        if break_at < max_chars // 2:
            break_at = max_chars
        else:
            break_at += 1  # include the trailing separator character

        parts.append(
            RawChunk(
                text=text[:break_at].strip(),
                page_start=page_start,
                page_end=page_end,
                section_title=section_title,
            )
        )
        text = text[break_at:].strip()

    if text:
        parts.append(
            RawChunk(
                text=text,
                page_start=page_start,
                page_end=page_end,
                section_title=section_title,
            )
        )
    return parts
