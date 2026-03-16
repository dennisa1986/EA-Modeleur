"""Unit tests for shared error codes and PipelineError."""

import pytest

from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError


@pytest.mark.unit
class TestPipelineError:
    def test_message_contains_code(self) -> None:
        err = PipelineError(ErrorCode.CANONICAL_MISSING_PROVENANCE, "no provenance")
        assert "CANON-002" in str(err)

    def test_context_defaults_to_empty_dict(self) -> None:
        err = PipelineError(ErrorCode.INGEST_READ_FAILURE, "boom")
        assert err.context == {}

    def test_context_is_stored(self) -> None:
        err = PipelineError(ErrorCode.META_001, "bad xmi", context={"path": "a.xmi"})
        assert err.context["path"] == "a.xmi"


@pytest.mark.unit
class TestErrorCode:
    def test_all_codes_are_unique(self) -> None:
        values = [e.value for e in ErrorCode]
        assert len(values) == len(set(values))
