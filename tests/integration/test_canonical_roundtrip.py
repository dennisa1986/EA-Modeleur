"""Integration tests for the canonical model layer.

Covers:
- JSON roundtrip from the minimal fixture
- Referential integrity (package_id, diagram element_id refs)
- Schema sync (fixture validates against the schema)
- Provenance requirement enforcement
- Builder API producing a realistic model
- Evidence and uncertainty in the full model
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.canonical.builders import CanonicalModelBuilder
from ea_mbse_pipeline.canonical.diagram_models import ElementBounds
from ea_mbse_pipeline.canonical.ids import new_id, to_ea_guid
from ea_mbse_pipeline.canonical.io import (
    load_canonical_model,
    save_canonical_model,
    validate_against_schema,
)
from ea_mbse_pipeline.canonical.models import (
    Attribute,
    CanonicalModel,
    ElementKind,
    ModelElement,
    Operation,
    Package,
    RelationshipKind,
    RequirementLinkType,
    TaggedValue,
)
from ea_mbse_pipeline.canonical.uncertainty_models import UncertaintyLevel, UncertaintyType
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef

FIXTURE_PATH = Path(__file__).parents[2] / "data" / "fixtures" / "canonical_minimal.json"


def _prov(file: str = "data/fixtures/canonical_minimal.json") -> Provenance:
    return Provenance(
        sources=[SourceRef(file_path=file)],
        derivation_method="test",
    )


# ---------------------------------------------------------------------------
# Schema sync test
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSchemaSync:
    def test_fixture_validates_against_schema(self) -> None:
        """The minimal fixture must validate against the authoritative schema."""
        import json

        with FIXTURE_PATH.open(encoding="utf-8") as fh:
            data = json.load(fh)
        validate_against_schema(data)  # must not raise

    def test_empty_model_validates_against_schema(self) -> None:
        import json

        model = CanonicalModel()
        data = model.model_dump(mode="json", exclude_none=True)
        validate_against_schema(data)

    def test_full_model_validates_against_schema(self, tmp_path: Path) -> None:
        """A model produced by the builder must round-trip through the schema validator."""
        model = _build_realistic_model()
        out = tmp_path / "full.json"
        save_canonical_model(model, out)  # validates internally
        loaded = load_canonical_model(out)
        assert len(loaded.elements) == len(model.elements)


# ---------------------------------------------------------------------------
# JSON roundtrip from fixture
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFixtureRoundtrip:
    def test_load_fixture(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        assert model.schema_version == "1.0"

    def test_fixture_has_expected_counts(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        assert len(model.packages) >= 2
        assert len(model.elements) >= 3
        assert len(model.relationships) >= 1
        assert len(model.diagrams) >= 1
        assert len(model.requirement_links) >= 1
        assert len(model.evidence_links) >= 1
        assert len(model.uncertainties) >= 1

    def test_roundtrip_preserves_element_names(self, tmp_path: Path) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        original_names = [e.name for e in model.elements]
        out = tmp_path / "roundtrip.json"
        save_canonical_model(model, out)
        reloaded = load_canonical_model(out)
        assert [e.name for e in reloaded.elements] == original_names

    def test_roundtrip_preserves_attributes(self, tmp_path: Path) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        sensor = next(e for e in model.elements if e.name == "Sensor")
        original_attr_names = [a.name for a in sensor.attributes]
        out = tmp_path / "rt2.json"
        save_canonical_model(model, out)
        reloaded = load_canonical_model(out)
        reloaded_sensor = next(e for e in reloaded.elements if e.name == "Sensor")
        assert [a.name for a in reloaded_sensor.attributes] == original_attr_names

    def test_roundtrip_preserves_diagram_objects(self, tmp_path: Path) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        diag = model.diagrams[0]
        original_element_ids = [o.element_id for o in diag.objects]
        out = tmp_path / "rt3.json"
        save_canonical_model(model, out)
        reloaded = load_canonical_model(out)
        reloaded_diag = reloaded.diagrams[0]
        assert [o.element_id for o in reloaded_diag.objects] == original_element_ids


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestReferentialIntegrity:
    def test_element_package_ids_are_valid(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        package_ids = {p.id for p in model.packages}
        for elem in model.elements:
            if elem.package_id is not None:
                assert elem.package_id in package_ids, (
                    f"Element {elem.name!r} references unknown package {elem.package_id!r}"
                )

    def test_package_parent_ids_are_valid(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        package_ids = {p.id for p in model.packages}
        for pkg in model.packages:
            if pkg.parent_id is not None:
                assert pkg.parent_id in package_ids, (
                    f"Package {pkg.name!r} references unknown parent {pkg.parent_id!r}"
                )

    def test_diagram_element_ids_exist(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        element_ids = {e.id for e in model.elements}
        package_ids = {p.id for p in model.packages}
        valid_ids = element_ids | package_ids
        for diag in model.diagrams:
            for obj in diag.objects:
                assert obj.element_id in valid_ids, (
                    f"DiagramObject in {diag.name!r} references unknown element {obj.element_id!r}"
                )

    def test_relationship_source_target_exist(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        element_ids = {e.id for e in model.elements}
        for rel in model.relationships:
            assert rel.source_id in element_ids, (
                f"Relationship {rel.id!r} source {rel.source_id!r} not found"
            )
            assert rel.target_id in element_ids, (
                f"Relationship {rel.id!r} target {rel.target_id!r} not found"
            )

    def test_evidence_links_point_to_existing_elements(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        all_ids = (
            {e.id for e in model.elements}
            | {p.id for p in model.packages}
            | {r.id for r in model.relationships}
            | {d.id for d in model.diagrams}
        )
        for ev in model.evidence_links:
            assert ev.element_id in all_ids, (
                f"EvidenceLink {ev.id!r} references unknown artefact {ev.element_id!r}"
            )

    def test_uncertainty_element_ids_exist(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        all_ids = (
            {e.id for e in model.elements}
            | {p.id for p in model.packages}
            | {r.id for r in model.relationships}
            | {d.id for d in model.diagrams}
        )
        for unc in model.uncertainties:
            assert unc.element_id in all_ids, (
                f"Uncertainty {unc.id!r} references unknown artefact {unc.element_id!r}"
            )

    def test_no_duplicate_ids(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        all_ids: list[str] = (
            [p.id for p in model.packages]
            + [e.id for e in model.elements]
            + [r.id for r in model.relationships]
            + [d.id for d in model.diagrams]
            + [rl.id for rl in model.requirement_links]
            + [ev.id for ev in model.evidence_links]
            + [u.id for u in model.uncertainties]
        )
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found in canonical model"


# ---------------------------------------------------------------------------
# Provenance requirement
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestProvenanceRequirement:
    def test_all_elements_have_provenance(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        for elem in model.elements:
            assert elem.provenance is not None, f"Element {elem.name!r} missing provenance"
            assert len(elem.provenance.sources) >= 1

    def test_all_packages_have_provenance(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        for pkg in model.packages:
            assert pkg.provenance is not None
            assert pkg.provenance.derivation_method != ""

    def test_all_relationships_have_provenance(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        for rel in model.relationships:
            assert rel.provenance is not None

    def test_all_diagrams_have_provenance(self) -> None:
        model = load_canonical_model(FIXTURE_PATH)
        for diag in model.diagrams:
            assert diag.provenance is not None


# ---------------------------------------------------------------------------
# Builder integration
# ---------------------------------------------------------------------------


def _build_realistic_model() -> CanonicalModel:
    """Helper: build a realistic model via the builder API."""
    prov = Provenance(
        sources=[SourceRef(file_path="data/fixtures/canonical_minimal.json")],
        derivation_method="builder-test",
    )

    pkg_id = new_id()
    sensor_id = new_id()
    collector_id = new_id()
    req_id = new_id()

    builder = CanonicalModelBuilder(source_description="Builder integration test")

    builder.add_package(id=pkg_id, name="System", provenance=prov)

    builder.add_element(
        id=sensor_id,
        kind=ElementKind.BLOCK,
        name="Sensor",
        package_id=pkg_id,
        attributes=[Attribute(id=new_id(), name="reading", type_name="float")],
        operations=[Operation(id=new_id(), name="measure", return_type="float")],
        tagged_values=[TaggedValue(name="version", value="1.0")],
        provenance=prov,
    )

    builder.add_element(
        id=collector_id,
        kind=ElementKind.CLASS,
        name="DataCollector",
        package_id=pkg_id,
        provenance=prov,
    )

    builder.add_element(
        id=req_id,
        kind=ElementKind.REQUIREMENT,
        name="REQ-001 Sampling Rate",
        package_id=pkg_id,
        provenance=prov,
    )

    builder.add_relationship(
        kind=RelationshipKind.ASSOCIATION,
        source_id=collector_id,
        target_id=sensor_id,
        name="monitors",
        provenance=prov,
    )

    builder.add_relationship(
        kind=RelationshipKind.SATISFY,
        source_id=sensor_id,
        target_id=req_id,
        provenance=prov,
    )

    diag_id = builder.add_diagram(
        name="System Overview",
        diagram_type="Logical",
        package_id=pkg_id,
        provenance=prov,
    )
    builder.add_diagram_object(
        diagram_id=diag_id,
        element_id=sensor_id,
        bounds=ElementBounds(x=100, y=100, width=120, height=60),
    )
    builder.add_diagram_object(
        diagram_id=diag_id,
        element_id=collector_id,
        bounds=ElementBounds(x=300, y=100, width=140, height=60),
    )

    builder.add_requirement_link(
        source_id=sensor_id,
        target_id=req_id,
        link_type=RequirementLinkType.SATISFIES,
        provenance=prov,
    )

    builder.add_evidence(
        element_id=sensor_id,
        provenance=prov,
        relevance_score=0.92,
        excerpt="Sensor block measures physical quantities.",
    )

    builder.add_uncertainty(
        element_id=collector_id,
        uncertainty_type=UncertaintyType.COMPLETENESS,
        level=UncertaintyLevel.LOW,
        description="Collector attributes may be incomplete.",
        mitigation="Review spec section 3.2.",
    )

    return builder.build()


@pytest.mark.integration
class TestBuilderIntegration:
    def test_builder_produces_valid_model(self) -> None:
        model = _build_realistic_model()
        assert len(model.packages) == 1
        assert len(model.elements) == 3
        assert len(model.relationships) == 2
        assert len(model.diagrams) == 1
        assert len(model.diagrams[0].objects) == 2
        assert len(model.requirement_links) == 1
        assert len(model.evidence_links) == 1
        assert len(model.uncertainties) == 1

    def test_builder_diagram_objects_have_bounds(self) -> None:
        model = _build_realistic_model()
        for obj in model.diagrams[0].objects:
            assert obj.bounds is not None

    def test_builder_missing_diagram_raises(self) -> None:
        prov = _prov()
        builder = CanonicalModelBuilder()
        with pytest.raises(PipelineError) as exc_info:
            builder.add_diagram_object(diagram_id="nonexistent", element_id="e1")
        assert exc_info.value.code == ErrorCode.CANONICAL_DANGLING_REFERENCE

    def test_builder_roundtrip(self, tmp_path: Path) -> None:
        model = _build_realistic_model()
        out = tmp_path / "builder_model.json"
        save_canonical_model(model, out)
        loaded = load_canonical_model(out)
        assert len(loaded.elements) == len(model.elements)
        assert loaded.elements[0].name == model.elements[0].name

    def test_ea_guid_conversion(self) -> None:
        uid = new_id()
        ea = to_ea_guid(uid)
        assert ea.startswith("{") and ea.endswith("}")
        assert uid.upper() == ea[1:-1]
