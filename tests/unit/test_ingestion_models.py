"""Unit tests for ingestion data models."""

from pathlib import Path

import pytest

from ea_pipeline.ingestion.models import InputKind, RawContent


@pytest.mark.unit
class TestRawContent:
    def test_text_input(self) -> None:
        rc = RawContent(source=Path("doc.txt"), kind=InputKind.TEXT, text="hello")
        assert rc.kind == InputKind.TEXT
        assert rc.text == "hello"

    def test_unknown_kind_default(self) -> None:
        rc = RawContent(source=Path("file.bin"), kind=InputKind.UNKNOWN)
        assert rc.text == ""
