"""Unit tests for ingestion data models."""

from pathlib import Path

import pytest

from ea_mbse_pipeline.ingest.models import InputKind, RawContent


@pytest.mark.unit
class TestRawContent:
    def test_text_input(self) -> None:
        rc = RawContent(source=Path("doc.txt"), kind=InputKind.TEXT, text="hello")
        assert rc.kind == InputKind.TEXT
        assert rc.text == "hello"
        assert rc.image_paths == []

    def test_image_kind(self) -> None:
        rc = RawContent(source=Path("screen.png"), kind=InputKind.IMAGE)
        assert rc.kind == InputKind.IMAGE

    def test_unknown_defaults(self) -> None:
        rc = RawContent(source=Path("file.bin"), kind=InputKind.UNKNOWN)
        assert rc.text == ""
        assert rc.metadata == {}
