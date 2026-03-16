"""Integration tests — wiring multiple stages together.

These tests use real (but minimal) implementations.
Skipped until stage implementations are available.
"""

import pytest


@pytest.mark.integration
class TestPipelineOrchestrator:
    @pytest.mark.skip(reason="Awaiting stage implementations — Sprint 1")
    def test_full_pipeline_text_input(self) -> None:
        """Full pipeline run with minimal text input produces an importable XMI."""
        ...

    @pytest.mark.skip(reason="Awaiting stage implementations — Sprint 1")
    def test_validation_error_halts_before_serialization(self) -> None:
        """An error-severity validation finding must prevent serialization."""
        ...

    @pytest.mark.skip(reason="Awaiting stage implementations — Sprint 1")
    def test_screenshot_element_requires_corroborating_source(self) -> None:
        """Elements sourced only from screenshots must fail provenance validation."""
        ...
