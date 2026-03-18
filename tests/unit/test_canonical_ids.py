"""Unit tests for canonical ID generation and EA GUID conversion."""

from __future__ import annotations

import uuid

import pytest

from ea_mbse_pipeline.canonical.ids import from_ea_guid, is_valid_id, new_id, to_ea_guid


@pytest.mark.unit
class TestNewId:
    def test_returns_string(self) -> None:
        assert isinstance(new_id(), str)

    def test_is_valid_uuid(self) -> None:
        uid = new_id()
        # Must not raise
        uuid.UUID(uid)

    def test_is_lowercase(self) -> None:
        uid = new_id()
        assert uid == uid.lower()

    def test_unique_on_each_call(self) -> None:
        ids = {new_id() for _ in range(100)}
        assert len(ids) == 100


@pytest.mark.unit
class TestToEaGuid:
    def test_wraps_in_braces(self) -> None:
        uid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        result = to_ea_guid(uid)
        assert result.startswith("{")
        assert result.endswith("}")

    def test_uppercases(self) -> None:
        uid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        result = to_ea_guid(uid)
        inner = result[1:-1]
        assert inner == inner.upper()

    def test_roundtrip_via_from(self) -> None:
        uid = new_id()
        assert from_ea_guid(to_ea_guid(uid)) == uid


@pytest.mark.unit
class TestFromEaGuid:
    def test_strips_braces(self) -> None:
        ea = "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"
        result = from_ea_guid(ea)
        assert not result.startswith("{")
        assert not result.endswith("}")

    def test_lowercases(self) -> None:
        ea = "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"
        result = from_ea_guid(ea)
        assert result == result.lower()

    def test_expected_value(self) -> None:
        ea = "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"
        assert from_ea_guid(ea) == "3fa85f64-5717-4562-b3fc-2c963f66afa6"


@pytest.mark.unit
class TestIsValidId:
    def test_valid_uuid4(self) -> None:
        assert is_valid_id(new_id()) is True

    def test_invalid_string(self) -> None:
        assert is_valid_id("not-a-uuid") is False

    def test_empty_string(self) -> None:
        assert is_valid_id("") is False

    def test_ea_guid_not_valid(self) -> None:
        # EA GUIDs have braces — not valid as pipeline-internal IDs
        ea = "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"
        assert is_valid_id(ea) is False
