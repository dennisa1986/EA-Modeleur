"""Unit tests for text and PDF chunking.

All tests are isolated — no filesystem or network access.
"""

from __future__ import annotations

import pytest

from ea_mbse_pipeline.ingest.chunking import (
    RawChunk,
    _is_heading,
    chunk_pdf_pages,
    chunk_text,
)
from ea_mbse_pipeline.ingest.pdf_extract import PageContent


@pytest.mark.unit
class TestIsHeading:
    def test_numbered_section_is_heading(self) -> None:
        assert _is_heading("1.2 System Architecture") is True

    def test_numbered_section_deep(self) -> None:
        assert _is_heading("3.1.4 Security Policies") is True

    def test_all_caps_short_is_heading(self) -> None:
        assert _is_heading("INTRODUCTION") is True

    def test_all_caps_long_is_heading(self) -> None:
        # isupper() + len >= 3 passes regardless of word count
        assert _is_heading("OVERVIEW") is True

    def test_title_case_no_punct_is_heading(self) -> None:
        assert _is_heading("System Components Overview") is True

    def test_sentence_ending_period_not_heading(self) -> None:
        assert _is_heading("This is a normal sentence.") is False

    def test_too_long_not_heading(self) -> None:
        assert _is_heading("A" * 130) is False

    def test_empty_not_heading(self) -> None:
        assert _is_heading("") is False

    def test_single_word_lowercase_not_heading(self) -> None:
        # Only one word: len(words) >= 2 fails
        assert _is_heading("overview") is False


@pytest.mark.unit
class TestChunkText:
    def test_single_paragraph_produces_chunk(self) -> None:
        text = (
            "Enterprise architecture components represent deployable units "
            "of software within the overall system topology."
        )
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert isinstance(chunks[0], RawChunk)

    def test_chunk_text_is_returned(self) -> None:
        text = (
            "This paragraph has enough characters to form a valid chunk "
            "because it contains more than eighty characters in total."
        )
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        combined = " ".join(c.text for c in chunks)
        assert "enough characters" in combined

    def test_numbered_section_splits_chunks(self) -> None:
        text = (
            "1. First Section\n"
            "This section contains content about the first topic with more than enough"
            " text to pass the minimum chunk size threshold required here.\n\n"
            "2. Second Section\n"
            "This section contains content about the second topic with more than enough"
            " text to pass the minimum chunk size threshold required here."
        )
        chunks = chunk_text(text)
        assert len(chunks) >= 2

    def test_section_titles_captured(self) -> None:
        text = (
            "1. Introduction\n"
            "This is the introduction content with more than enough characters"
            " to pass the minimum chunk size threshold for a valid chunk.\n\n"
            "2. Background\n"
            "This is the background section content with more than enough characters"
            " to pass the minimum chunk size threshold for a valid chunk here."
        )
        chunks = chunk_text(text)
        titles = [c.section_title for c in chunks if c.section_title]
        assert any("Introduction" in (t or "") for t in titles) or any(
            "Background" in (t or "") for t in titles
        )

    def test_empty_text_returns_no_chunks(self) -> None:
        assert chunk_text("   \n  ") == []

    def test_whitespace_only_returns_no_chunks(self) -> None:
        assert chunk_text("\n\n\n") == []

    def test_page_numbers_are_none_for_text(self) -> None:
        text = "This is content long enough to form a valid chunk in the system."
        chunks = chunk_text(text)
        for chunk in chunks:
            assert chunk.page_start is None
            assert chunk.page_end is None

    def test_short_text_below_minimum_returns_no_chunks(self) -> None:
        # Below _MIN_CHUNK_CHARS (80) threshold
        chunks = chunk_text("Too short.", min_chars=80)
        assert chunks == []

    def test_oversized_chunk_is_split(self) -> None:
        # A very long text should be split into multiple chunks
        long_text = ("Architecture components represent deployable units. " * 100)
        chunks = chunk_text(long_text, max_chars=200)
        assert len(chunks) > 1

    def test_multiple_blank_line_paragraphs(self) -> None:
        text = (
            "First paragraph with substantial content about architecture.\n\n"
            "Second paragraph with more content about components and interfaces.\n\n"
            "Third paragraph wrapping up the section with final details."
        )
        chunks = chunk_text(text)
        assert len(chunks) >= 1


@pytest.mark.unit
class TestChunkPdfPages:
    def test_chunks_from_two_pages(self) -> None:
        pages = [
            PageContent(
                page_number=1,
                text=(
                    "1. Introduction\n"
                    "This is the introduction content with more than enough characters"
                    " to exceed the minimum chunk size threshold for a valid chunk here."
                ),
            ),
            PageContent(
                page_number=2,
                text=(
                    "2. Main Body\n"
                    "This is the main body section content with more than enough characters"
                    " to exceed the minimum chunk size threshold for a valid chunk here."
                ),
            ),
        ]
        chunks = chunk_pdf_pages(pages)
        assert len(chunks) >= 1

    def test_page_numbers_are_set_on_chunks(self) -> None:
        pages = [
            PageContent(
                page_number=5,
                text=(
                    "This is substantial page text content that exceeds the minimum "
                    "threshold size requirement for a valid chunk to be included."
                ),
            ),
        ]
        chunks = chunk_pdf_pages(pages)
        assert len(chunks) >= 1
        for chunk in chunks:
            # At least one of the page fields is set
            assert chunk.page_start == 5 or chunk.page_end == 5

    def test_empty_pages_returns_no_chunks(self) -> None:
        pages = [PageContent(page_number=1, text="")]
        assert chunk_pdf_pages(pages) == []

    def test_empty_page_list_returns_no_chunks(self) -> None:
        assert chunk_pdf_pages([]) == []

    def test_heading_starts_new_chunk(self) -> None:
        pages = [
            PageContent(
                page_number=1,
                text=(
                    "1. First Chapter\n"
                    "Content for first chapter with more than enough text here"
                    " to exceed the minimum chunk size threshold for valid chunks.\n"
                    "2. Second Chapter\n"
                    "Content for second chapter with more than enough text here"
                    " to exceed the minimum chunk size threshold for valid chunks."
                ),
            ),
        ]
        chunks = chunk_pdf_pages(pages)
        assert len(chunks) >= 2

    def test_result_type(self) -> None:
        pages = [
            PageContent(
                page_number=1,
                text="Some page content that is long enough to pass the minimum threshold.",
            ),
        ]
        chunks = chunk_pdf_pages(pages)
        assert all(isinstance(c, RawChunk) for c in chunks)
