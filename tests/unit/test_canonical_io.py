"""Unit tests for canonical model JSON I/O and schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ea_mbse_pipeline.canonical.io import (
    load_canonical_model,
    save_canonical_model,
    validate_against_schema,
)
from ea_mbse_pipeline.canonical.models import (
    CanonicalModel,
    ElementKind,
    ModelElement,
    RelationshipKind,
)
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef


def _prov() -> Provenance:
    return Provenance(sources=[SourceRef(file_path="test.txt")], derivation_method="test")


def _minimal_model() -> CanonicalModel:
    return CanonicalModel(
        source_description="unit-test model",
        elements=[
            ModelElement(id="e1", kind=ElementKind.CLASS, name="A", provenance=_prov()),
            ModelElement(id="e2", kind=ElementKind.CLASS, name="B", provenance=_prov()),
        ],
    )


# ---------------------------------------------------------------------------
# validate_against_schema
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateAgainstSchema:
    def test_valid_minimal(self) -> None:
        data = {
            "schema_version": "1.0",
            "elements": [],
            "relationships": [],
            "diagrams": [],
        }
        # Must not raise
        validate_against_schema(data)

    def test_missing_required_field_raises(self) -> None:
        data = {
            "schema_version": "1.0",
            "elements": [],
            "relationships": [],
            # "diagrams" is missing
        }
        with pytest.raises(PipelineError) as exc_info:
            validate_against_schema(data)
        assert exc_info.value.code == ErrorCode.CANONICAL_SCHEMA_VIOLATION

    def test_invalid_element_kind_raises(self) -> None:
        data = {
            "schema_version": "1.0",
            "elements": [
                {
                    "id": "e1",
                    "kind": "InvalidKind",
                    "name": "X",
                    "provenance": {
                        "sources": [{"file_path": "f.txt"}],
                        "derivation_method": "test",
                    },
                }
            ],
            "relationships": [],
            "diagrams": [],
        }
        with pytest.raises(PipelineError) as exc_info:
            validate_against_schema(data)
        assert exc_info.value.code == ErrorCode.CANONICAL_SCHEMA_VIOLATION

    def test_element_missing_provenance_raises(self) -> None:
        data = {
            "schema_version": "1.0",
            "elements": [{"id": "e1", "kind": "Class", "name": "X"}],
            "relationships": [],
            "diagrams": [],
        }
        with pytest.raises(PipelineError) as exc_info:
            validate_against_schema(data)
        assert exc_info.value.code == ErrorCode.CANONICAL_SCHEMA_VIOLATION


# ---------------------------------------------------------------------------
# save_canonical_model + load_canonical_model
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSaveLoad:
    def test_roundtrip(self, tmp_path: Path) -> None:
        model = _minimal_model()
        out = tmp_path / "model.json"
        save_canonical_model(model, out)
        loaded = load_canonical_model(out)
        assert len(loaded.elements) == 2
        assert loaded.elements[0].name == "A"
        assert loaded.schema_version == "1.0"

    def test_saved_file_is_valid_json(self, tmp_path: Path) -> None:
        model = _minimal_model()
        out = tmp_path / "model.json"
        save_canonical_model(model, out)
        with out.open(encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, dict)
        assert data["schema_version"] == "1.0"

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(PipelineError) as exc_info:
            load_canonical_model(missing)
        assert exc_info.value.code == ErrorCode.CANONICAL_IO_READ_FAIL

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not valid JSON {{{", encoding="utf-8")
        with pytest.raises(PipelineError) as exc_info:
            load_canonical_model(bad)
        assert exc_info.value.code == ErrorCode.CANONICAL_IO_READ_FAIL

    def test_load_schema_violation_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad_schema.json"
        bad.write_text(
            json.dumps({"schema_version": "1.0", "elements": [], "relationships": []}),
            encoding="utf-8",
        )
        with pytest.raises(PipelineError) as exc_info:
            load_canonical_model(bad)
        assert exc_info.value.code == ErrorCode.CANONICAL_SCHEMA_VIOLATION

    def test_roundtrip_preserves_attributes(self, tmp_path: Path) -> None:
        from ea_mbse_pipeline.canonical.models import Attribute, Operation, TaggedValue

        model = CanonicalModel(
            elements=[
                ModelElement(
                    id="e1",
                    kind=ElementKind.CLASS,
                    name="Sensor",
                    attributes=[Attribute(id="a1", name="reading", type_name="float")],
                    operations=[Operation(id="op1", name="measure", return_type="float")],
                    tagged_values=[TaggedValue(name="k", value="v")],
                    provenance=_prov(),
                )
            ]
        )
        out = tmp_path / "sensor.json"
        save_canonical_model(model, out)
        loaded = load_canonical_model(out)
        elem = loaded.elements[0]
        assert isinstance(elem.attributes[0].type_name, str)
        assert elem.attributes[0].type_name == "float"
        assert elem.operations[0].return_type == "float"
        assert elem.tagged_values[0].name == "k"

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c" / "model.json"
        save_canonical_model(_minimal_model(), nested)
        assert nested.exists()
