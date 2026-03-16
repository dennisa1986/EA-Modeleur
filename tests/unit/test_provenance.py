"""Unit tests for provenance models."""

import pytest

from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef


@pytest.mark.unit
class TestProvenance:
    def test_minimal_provenance(self) -> None:
        prov = Provenance(
            sources=[SourceRef(file_path="doc.pdf", page=3)],
            derivation_method="text-extraction",
        )
        assert prov.sources[0].page == 3
        assert prov.confidence is None

    def test_confidence_stored(self) -> None:
        prov = Provenance(
            sources=[SourceRef(file_path="img.png")],
            derivation_method="ocr",
            confidence=0.87,
        )
        assert prov.confidence == pytest.approx(0.87)
