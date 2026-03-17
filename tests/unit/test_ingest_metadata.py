"""Unit tests for metadata construction and keyword extraction.

All tests are isolated — no network access.  Tests that create files use
pytest's tmp_path fixture.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ea_mbse_pipeline.ingest.chunking import RawChunk
from ea_mbse_pipeline.ingest.metadata import (
    build_corpus_chunk,
    build_source_document,
    doc_id_from_path,
    extract_keywords,
)
from ea_mbse_pipeline.ingest.models import InputKind


@pytest.mark.unit
class TestExtractKeywords:
    def test_returns_list(self) -> None:
        result = extract_keywords("enterprise architecture component interface dependency")
        assert isinstance(result, list)

    def test_stop_words_excluded(self) -> None:
        result = extract_keywords("the quick brown foxes jump over the lazy dogs")
        assert "the" not in result
        assert "over" not in result

    def test_max_keywords_respected(self) -> None:
        text = " ".join(
            ["architecture"] * 10
            + ["component"] * 8
            + ["interface"] * 6
            + [f"wordextra{i}" for i in range(20)]
        )
        result = extract_keywords(text, max_keywords=5)
        assert len(result) <= 5

    def test_most_frequent_first(self) -> None:
        text = "component component component architecture architecture interface"
        result = extract_keywords(text)
        assert result[0] == "component"

    def test_empty_text_returns_empty(self) -> None:
        assert extract_keywords("") == []

    def test_short_tokens_excluded(self) -> None:
        # Tokens must be length >= 4 (regex [a-z]{3,} after first char)
        result = extract_keywords("cat dog fox bee")
        assert result == []

    def test_case_insensitive(self) -> None:
        result = extract_keywords("Architecture architecture ARCHITECTURE")
        assert "architecture" in result

    def test_numbers_not_included(self) -> None:
        result = extract_keywords("12345 6789 component")
        assert all(kw.isalpha() for kw in result)


@pytest.mark.unit
class TestDocIdFromPath:
    def test_deterministic(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world content")
        id1 = doc_id_from_path(f)
        id2 = doc_id_from_path(f)
        assert id1 == id2

    def test_starts_with_doc_prefix(self, tmp_path: Path) -> None:
        f = tmp_path / "document.txt"
        f.write_text("content here")
        assert doc_id_from_path(f).startswith("doc-")

    def test_hex_suffix_length(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("data")
        doc_id = doc_id_from_path(f)
        suffix = doc_id.removeprefix("doc-")
        assert len(suffix) == 16
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_different_content_different_ids(self, tmp_path: Path) -> None:
        f1 = tmp_path / "file_alpha.txt"
        f2 = tmp_path / "file_beta.txt"
        f1.write_text("content_a" * 100)
        f2.write_text("content_b_different" * 100)
        assert doc_id_from_path(f1) != doc_id_from_path(f2)

    def test_missing_file_does_not_raise(self, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.txt"
        # Should not raise even though file doesn't exist
        result = doc_id_from_path(f)
        assert result.startswith("doc-")

    def test_same_name_same_content_same_id(self, tmp_path: Path) -> None:
        """Same filename + same content → same doc_id regardless of directory."""
        d1 = tmp_path / "dir1"
        d2 = tmp_path / "dir2"
        d1.mkdir()
        d2.mkdir()
        content = b"identical content bytes for fingerprinting" * 100
        (d1 / "report.pdf").write_bytes(content)
        (d2 / "report.pdf").write_bytes(content)
        assert doc_id_from_path(d1 / "report.pdf") == doc_id_from_path(d2 / "report.pdf")

    def test_same_name_different_content_different_id(self, tmp_path: Path) -> None:
        """Same filename but different content → different doc_id."""
        d1 = tmp_path / "dir1"
        d2 = tmp_path / "dir2"
        d1.mkdir()
        d2.mkdir()
        (d1 / "doc.txt").write_text("version A content is distinct here")
        (d2 / "doc.txt").write_text("version B content is completely different")
        assert doc_id_from_path(d1 / "doc.txt") != doc_id_from_path(d2 / "doc.txt")

    def test_content_change_changes_id(self, tmp_path: Path) -> None:
        """Modifying a file's content produces a new doc_id on next call."""
        f = tmp_path / "mutable.txt"
        f.write_text("original content version one")
        id_before = doc_id_from_path(f)
        f.write_text("completely changed content version two")
        id_after = doc_id_from_path(f)
        assert id_before != id_after

    def test_large_file_stable_id(self, tmp_path: Path) -> None:
        """doc_id is stable for large files (fingerprint reads at most 64 KiB)."""
        f = tmp_path / "large.bin"
        f.write_bytes(b"x" * 200_000)
        assert doc_id_from_path(f) == doc_id_from_path(f)


@pytest.mark.unit
class TestBuildSourceDocument:
    def test_basic_text_document(self, tmp_path: Path) -> None:
        f = tmp_path / "corpus.txt"
        f.write_text("some content here with enough text")
        doc = build_source_document(f, InputKind.TEXT, char_count=34)
        assert doc.file_name == "corpus.txt"
        assert doc.source_type == InputKind.TEXT
        assert doc.char_count == 34
        assert doc.doc_id.startswith("doc-")

    def test_pdf_with_page_count(self, tmp_path: Path) -> None:
        f = tmp_path / "document.pdf"
        f.write_bytes(b"%PDF-1.4 minimal content")
        doc = build_source_document(f, InputKind.PDF, page_count=42)
        assert doc.page_count == 42
        assert doc.source_type == InputKind.PDF

    def test_extra_metadata_stored(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        doc = build_source_document(
            f, InputKind.PDF, extra_metadata={"title": "Test Framework"}
        )
        assert doc.metadata["title"] == "Test Framework"

    def test_file_size_recorded(self, tmp_path: Path) -> None:
        content = "x" * 1024
        f = tmp_path / "sized.txt"
        f.write_text(content)
        doc = build_source_document(f, InputKind.TEXT)
        assert doc.file_size_bytes == 1024

    def test_file_path_stored(self, tmp_path: Path) -> None:
        f = tmp_path / "stored.txt"
        f.write_text("content")
        doc = build_source_document(f, InputKind.TEXT)
        assert str(f) in doc.file_path


@pytest.mark.unit
class TestBuildCorpusChunk:
    def test_chunk_fields_populated(self, tmp_path: Path) -> None:
        f = tmp_path / "source.txt"
        f.write_text("text")
        raw = RawChunk(
            text="This is a substantial text chunk for testing purposes here.",
            page_start=1,
            page_end=1,
            section_title="Introduction",
        )
        chunk = build_corpus_chunk(raw, "doc-abc123", str(f), InputKind.TEXT)
        assert chunk.doc_id == "doc-abc123"
        assert chunk.section_title == "Introduction"
        assert chunk.page_start == 1
        assert chunk.page_end == 1
        assert chunk.char_count == len(raw.text)
        assert chunk.text == raw.text

    def test_provenance_source_set(self, tmp_path: Path) -> None:
        f = tmp_path / "source.txt"
        f.write_text("content")
        raw = RawChunk(
            text="Chunk text content here for testing provenance tracking.",
            page_start=3,
            page_end=3,
            section_title="Section 2",
        )
        chunk = build_corpus_chunk(raw, "doc-xyz", str(f), InputKind.TEXT)
        assert len(chunk.provenance_sources) == 1
        assert chunk.provenance_sources[0].file_path == str(f)
        assert chunk.provenance_sources[0].page == 3
        assert chunk.provenance_sources[0].region == "Section 2"

    def test_chunk_id_is_uuid4_format(self, tmp_path: Path) -> None:
        f = tmp_path / "source.txt"
        f.write_text("content")
        raw = RawChunk(
            text="Chunk text that is long enough to pass validation checks.",
            page_start=None,
            page_end=None,
            section_title=None,
        )
        chunk = build_corpus_chunk(raw, "doc-123", str(f), InputKind.TEXT)
        assert re.match(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            chunk.chunk_id,
        )

    def test_keywords_extracted(self, tmp_path: Path) -> None:
        f = tmp_path / "source.txt"
        f.write_text("content")
        raw = RawChunk(
            text=(
                "Architecture components represent deployable infrastructure "
                "components that serve important architecture functions."
            ),
            page_start=None,
            page_end=None,
            section_title=None,
        )
        chunk = build_corpus_chunk(raw, "doc-kw", str(f), InputKind.TEXT)
        assert len(chunk.detected_keywords) > 0
        # "components" or "architecture" should appear (most frequent)
        assert any(kw in ("components", "architecture", "deployable") for kw in chunk.detected_keywords)

    def test_source_type_preserved(self, tmp_path: Path) -> None:
        f = tmp_path / "source.pdf"
        f.write_bytes(b"%PDF-1.4")
        raw = RawChunk(
            text="PDF chunk content that is long enough to be a valid chunk.",
            page_start=2,
            page_end=2,
            section_title=None,
        )
        chunk = build_corpus_chunk(raw, "doc-pdf", str(f), InputKind.PDF)
        assert chunk.source_type == InputKind.PDF
