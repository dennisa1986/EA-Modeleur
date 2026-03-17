"""Metadata construction for corpus chunks and source documents.

Provides:
  doc_id_from_path(path)          — deterministic document ID
  extract_keywords(text)          — simple frequency-based keyword extraction
  build_source_document(...)      — build a SourceDocument from a file path
  build_corpus_chunk(raw, ...)    — attach metadata to a RawChunk → CorpusChunk

Keyword extraction is intentionally simple (no NLP libraries): frequency-ranked
tokens after stop-word filtering.  Domain-specific tagging (object_type,
discipline) is left as None — downstream stages or human operators can enrich
these fields.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

from ea_mbse_pipeline.ingest.chunking import RawChunk
from ea_mbse_pipeline.ingest.models import CorpusChunk, InputKind, SourceDocument
from ea_mbse_pipeline.shared.logging import get_logger
from ea_mbse_pipeline.shared.provenance import SourceRef

logger = get_logger(__name__)

# Common English stop words — excluded from keyword extraction
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "not",
    "that", "this", "these", "those", "it", "its", "as", "so", "if",
    "then", "than", "when", "where", "which", "who", "what", "how",
    "also", "more", "their", "they", "them", "there", "here", "just",
    "each", "about", "into", "over", "after", "before", "between",
    "through", "during", "under", "while", "such", "very", "used",
})


# Number of bytes read from the file for the content fingerprint.
# 64 KiB is large enough to distinguish real-world documents while remaining
# fast even on network-mounted storage.
_FINGERPRINT_BYTES: int = 65_536


def doc_id_from_path(path: Path) -> str:
    """Derive a deterministic document ID from the file name and content prefix.

    Strategy: SHA-256 of ``<filename_bytes> + b":" + <first 64 KiB of content>``.

    This is:
    - **Collision-resistant**: two files with the same name but different
      content produce different IDs; two files with different names but
      identical content also produce different IDs (name is included in the
      hash input).
    - **Stable**: re-ingesting the same unchanged file always yields the same
      ``doc_id``, enabling idempotent upserts in SQLite.
    - **Fast**: at most 64 KiB is read, regardless of file size.

    Fallback: if the file cannot be read (e.g. missing or permission error),
    the strategy degrades to ``SHA-256(<filename>:<stat.st_size>)``, with size
    defaulting to 0 for non-existent files.  This preserves the "no raise"
    contract while flagging the degraded case in the log.

    Returns:
        String of the form ``"doc-<16 hex chars>"``.
    """
    try:
        content_prefix = path.read_bytes()[:_FINGERPRINT_BYTES]
        key = path.name.encode() + b":" + content_prefix
    except OSError:
        # Fallback: name + size (legacy behaviour, used only when file is
        # unreadable, e.g. in tests that pass non-existent paths).
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        logger.debug(
            "doc_id fallback (unreadable file '%s'): using name+size strategy",
            path.name,
        )
        key = f"{path.name}:{size}".encode()
    digest = hashlib.sha256(key).hexdigest()[:16]
    return f"doc-{digest}"


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """Extract the top-*max_keywords* most frequent non-stop-word tokens.

    Tokens must be alphabetic, start with a letter, and have length ≥ 4.
    Returned in descending frequency order.

    Args:
        text:         Input text.
        max_keywords: Maximum number of keywords to return.

    Returns:
        List of lowercase keyword strings.
    """
    words = re.findall(r"\b[A-Za-z][a-z]{3,}\b", text)
    counts: dict[str, int] = {}
    for word in words:
        lower = word.lower()
        if lower not in _STOP_WORDS:
            counts[lower] = counts.get(lower, 0) + 1
    return sorted(counts, key=lambda w: counts[w], reverse=True)[:max_keywords]


def build_source_document(
    path: Path,
    source_type: InputKind,
    page_count: int | None = None,
    char_count: int | None = None,
    extra_metadata: dict[str, str] | None = None,
) -> SourceDocument:
    """Build a SourceDocument record for the given file.

    Args:
        path:           Path to the source file.
        source_type:    InputKind enum value.
        page_count:     Number of pages (PDF only).
        char_count:     Total extracted character count.
        extra_metadata: Additional format-specific metadata (title, author, …).

    Returns:
        A populated SourceDocument instance.
    """
    try:
        size = path.stat().st_size
    except OSError:
        size = 0

    return SourceDocument(
        doc_id=doc_id_from_path(path),
        file_path=str(path),
        file_name=path.name,
        source_type=source_type,
        file_size_bytes=size,
        page_count=page_count,
        char_count=char_count,
        metadata=extra_metadata or {},
    )


def build_corpus_chunk(
    raw: RawChunk,
    doc_id: str,
    source_file: str,
    source_type: InputKind,
) -> CorpusChunk:
    """Attach metadata to a RawChunk and produce a CorpusChunk.

    Assigns a fresh UUID chunk_id, extracts keywords, and builds a SourceRef
    for downstream provenance tracking.

    Args:
        raw:         RawChunk from chunking.py.
        doc_id:      Owning document ID.
        source_file: Path string of the originating file.
        source_type: InputKind of the originating file.

    Returns:
        A fully populated CorpusChunk instance.
    """
    keywords = extract_keywords(raw.text)
    provenance = SourceRef(
        file_path=source_file,
        page=raw.page_start,
        region=raw.section_title,
    )
    return CorpusChunk(
        chunk_id=str(uuid4()),
        doc_id=doc_id,
        source_file=source_file,
        source_type=source_type,
        page_start=raw.page_start,
        page_end=raw.page_end,
        section_title=raw.section_title,
        text=raw.text,
        char_count=len(raw.text),
        detected_keywords=keywords,
        provenance_sources=[provenance],
    )
