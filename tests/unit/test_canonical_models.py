"""Unit tests for canonical model data models — Sprint 4 extended suite."""

from __future__ import annotations

import pytest

from ea_mbse_pipeline.canonical.diagram_models import (
    DiagramObject,
    ElementBounds,
    ModelDiagram,
)
from ea_mbse_pipeline.canonical.evidence_models import EvidenceLink
from ea_mbse_pipeline.canonical.models import (
    Attribute,
    CanonicalModel,
    ElementKind,
    ModelElement,
    ModelRelationship,
    Operation,
    Package,
    Parameter,
    ParameterDirection,
    RelationshipKind,
    RequirementLink,
    RequirementLinkType,
    TaggedValue,
    Visibility,
)
from ea_mbse_pipeline.canonical.uncertainty_models import (
    Uncertainty,
    UncertaintyLevel,
    UncertaintyType,
)
from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prov(method: str = "test", file: str = "test.txt") -> Provenance:
    return Provenance(
        sources=[SourceRef(file_path=file)],
        derivation_method=method,
    )


# ---------------------------------------------------------------------------
# TaggedValue
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaggedValue:
    def test_basic(self) -> None:
        tv = TaggedValue(name="version", value="2.0")
        assert tv.name == "version"
        assert tv.value == "2.0"
        assert tv.notes == ""

    def test_with_notes(self) -> None:
        tv = TaggedValue(name="status", value="open", notes="Pending review")
        assert tv.notes == "Pending review"


# ---------------------------------------------------------------------------
# Parameter & Attribute & Operation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParameter:
    def test_defaults(self) -> None:
        p = Parameter(id="p1", name="x")
        assert p.direction == ParameterDirection.IN
        assert p.type_name is None
        assert p.default_value is None

    def test_explicit_direction(self) -> None:
        p = Parameter(id="p2", name="result", direction=ParameterDirection.OUT)
        assert p.direction == ParameterDirection.OUT


@pytest.mark.unit
class TestAttribute:
    def test_defaults(self) -> None:
        a = Attribute(id="a1", name="reading")
        assert a.visibility == Visibility.PUBLIC
        assert a.type_name is None
        assert a.initial_value is None
        assert a.tagged_values == []

    def test_full(self) -> None:
        a = Attribute(
            id="a2",
            name="unit",
            type_name="string",
            visibility=Visibility.PRIVATE,
            initial_value="celsius",
            tagged_values=[TaggedValue(name="k", value="v")],
        )
        assert a.type_name == "string"
        assert a.visibility == Visibility.PRIVATE
        assert len(a.tagged_values) == 1


@pytest.mark.unit
class TestOperation:
    def test_defaults(self) -> None:
        op = Operation(id="op1", name="measure")
        assert op.return_type is None
        assert op.visibility == Visibility.PUBLIC
        assert op.parameters == []
        assert op.tagged_values == []

    def test_with_parameters(self) -> None:
        op = Operation(
            id="op2",
            name="collect",
            return_type="list",
            parameters=[Parameter(id="p1", name="sensors", type_name="list[Sensor]")],
        )
        assert len(op.parameters) == 1
        assert op.parameters[0].name == "sensors"


# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPackage:
    def test_root_package(self) -> None:
        pkg = Package(id="pkg1", name="Root", provenance=_prov())
        assert pkg.parent_id is None
        assert pkg.path == ""
        assert pkg.stereotype is None

    def test_child_package(self) -> None:
        child = Package(
            id="pkg2", name="Domain", parent_id="pkg1", path="Root.Domain", provenance=_prov()
        )
        assert child.parent_id == "pkg1"
        assert child.path == "Root.Domain"

    def test_requires_provenance(self) -> None:
        with pytest.raises(Exception):
            Package(id="pkg3", name="Bad")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ModelElement
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModelElement:
    def test_element_requires_provenance(self) -> None:
        elem = ModelElement(id="e1", kind=ElementKind.CLASS, name="Foo", provenance=_prov())
        assert elem.provenance.derivation_method == "test"

    def test_defaults(self) -> None:
        elem = ModelElement(id="e1", kind=ElementKind.COMPONENT, name="C", provenance=_prov())
        assert elem.attributes == []
        assert elem.operations == []
        assert elem.tagged_values == []
        assert elem.stereotype is None
        assert elem.package_id is None
        assert elem.ea_guid is None

    def test_typed_attributes(self) -> None:
        elem = ModelElement(
            id="e2",
            kind=ElementKind.CLASS,
            name="Sensor",
            attributes=[Attribute(id="a1", name="reading", type_name="float")],
            provenance=_prov(),
        )
        assert elem.attributes[0].type_name == "float"
        assert isinstance(elem.attributes[0], Attribute)

    def test_typed_operations(self) -> None:
        elem = ModelElement(
            id="e3",
            kind=ElementKind.CLASS,
            name="Sensor",
            operations=[Operation(id="op1", name="measure", return_type="float")],
            provenance=_prov(),
        )
        assert isinstance(elem.operations[0], Operation)

    def test_typed_tagged_values(self) -> None:
        elem = ModelElement(
            id="e4",
            kind=ElementKind.CLASS,
            name="X",
            tagged_values=[TaggedValue(name="k", value="v")],
            provenance=_prov(),
        )
        assert isinstance(elem.tagged_values[0], TaggedValue)
        assert elem.tagged_values[0].name == "k"

    def test_package_id_field(self) -> None:
        elem = ModelElement(
            id="e5", kind=ElementKind.CLASS, name="Y", package_id="pkg-uuid", provenance=_prov()
        )
        assert elem.package_id == "pkg-uuid"

    def test_extended_element_kinds(self) -> None:
        for kind in [ElementKind.REQUIREMENT, ElementKind.BLOCK, ElementKind.ACTIVITY, ElementKind.STATE]:
            elem = ModelElement(id="e6", kind=kind, name="X", provenance=_prov())
            assert elem.kind == kind


# ---------------------------------------------------------------------------
# ModelRelationship
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModelRelationship:
    def test_basic(self) -> None:
        rel = ModelRelationship(
            id="r1",
            kind=RelationshipKind.ASSOCIATION,
            source_id="e1",
            target_id="e2",
            provenance=_prov(),
        )
        assert rel.name == ""
        assert rel.tagged_values == []
        assert isinstance(rel.tagged_values, list)

    def test_extended_relationship_kinds(self) -> None:
        for kind in [
            RelationshipKind.TRACE,
            RelationshipKind.REFINE,
            RelationshipKind.DERIVE,
            RelationshipKind.SATISFY,
            RelationshipKind.VERIFY,
        ]:
            rel = ModelRelationship(
                id="r2", kind=kind, source_id="e1", target_id="e2", provenance=_prov()
            )
            assert rel.kind == kind


# ---------------------------------------------------------------------------
# RequirementLink
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRequirementLink:
    def test_basic(self) -> None:
        link = RequirementLink(
            id="rl1",
            source_id="elem-a",
            target_id="req-b",
            link_type=RequirementLinkType.SATISFIES,
            provenance=_prov(),
        )
        assert link.link_type == RequirementLinkType.SATISFIES
        assert link.notes == ""

    def test_all_link_types(self) -> None:
        for lt in RequirementLinkType:
            link = RequirementLink(
                id="rl2", source_id="a", target_id="b", link_type=lt, provenance=_prov()
            )
            assert link.link_type == lt


# ---------------------------------------------------------------------------
# DiagramObject, ElementBounds, ModelDiagram
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiagramModels:
    def test_element_bounds_defaults(self) -> None:
        b = ElementBounds()
        assert b.x == 0
        assert b.width == 100
        assert b.height == 60

    def test_diagram_object_no_bounds(self) -> None:
        obj = DiagramObject(id="do1", element_id="e1")
        assert obj.bounds is None

    def test_diagram_object_with_bounds(self) -> None:
        obj = DiagramObject(
            id="do2",
            element_id="e1",
            bounds=ElementBounds(x=10, y=20, width=80, height=50),
        )
        assert obj.bounds is not None
        assert obj.bounds.x == 10

    def test_model_diagram(self) -> None:
        diag = ModelDiagram(
            id="d1",
            name="Overview",
            diagram_type="Logical",
            package_id="pkg1",
            objects=[DiagramObject(id="do1", element_id="e1")],
            provenance=_prov(),
        )
        assert diag.package_id == "pkg1"
        assert len(diag.objects) == 1

    def test_diagram_package_id_optional(self) -> None:
        diag = ModelDiagram(id="d2", name="Root Diag", diagram_type="Component", provenance=_prov())
        assert diag.package_id is None
        assert diag.objects == []


# ---------------------------------------------------------------------------
# EvidenceLink
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEvidenceLink:
    def test_basic(self) -> None:
        ev = EvidenceLink(id="ev1", element_id="e1", provenance=_prov())
        assert ev.relevance_score is None
        assert ev.excerpt == ""

    def test_with_score_and_excerpt(self) -> None:
        ev = EvidenceLink(
            id="ev2",
            element_id="e1",
            provenance=_prov(),
            relevance_score=0.87,
            excerpt="The sensor measures temperature.",
        )
        assert ev.relevance_score == pytest.approx(0.87)
        assert "sensor" in ev.excerpt

    def test_score_out_of_bounds_raises(self) -> None:
        with pytest.raises(Exception):
            EvidenceLink(id="ev3", element_id="e1", provenance=_prov(), relevance_score=1.5)


# ---------------------------------------------------------------------------
# Uncertainty
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUncertainty:
    def test_basic(self) -> None:
        u = Uncertainty(
            id="u1",
            element_id="e1",
            uncertainty_type=UncertaintyType.COMPLETENESS,
            level=UncertaintyLevel.LOW,
            description="May be incomplete.",
        )
        assert u.mitigation == ""

    def test_all_types_and_levels(self) -> None:
        for utype in UncertaintyType:
            for level in UncertaintyLevel:
                u = Uncertainty(
                    id="u2",
                    element_id="x",
                    uncertainty_type=utype,
                    level=level,
                    description="test",
                )
                assert u.uncertainty_type == utype
                assert u.level == level


# ---------------------------------------------------------------------------
# CanonicalModel (root container)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCanonicalModel:
    def test_empty_model(self) -> None:
        model = CanonicalModel()
        assert model.elements == []
        assert model.relationships == []
        assert model.diagrams == []
        assert model.packages == []
        assert model.requirement_links == []
        assert model.evidence_links == []
        assert model.uncertainties == []
        assert model.schema_version == "1.0"

    def test_model_with_relationship(self) -> None:
        prov = _prov()
        model = CanonicalModel(
            elements=[
                ModelElement(id="e1", kind=ElementKind.CLASS, name="A", provenance=prov),
                ModelElement(id="e2", kind=ElementKind.CLASS, name="B", provenance=prov),
            ],
            relationships=[
                ModelRelationship(
                    id="r1",
                    kind=RelationshipKind.ASSOCIATION,
                    source_id="e1",
                    target_id="e2",
                    provenance=prov,
                )
            ],
        )
        assert len(model.relationships) == 1

    def test_model_with_packages(self) -> None:
        prov = _prov()
        model = CanonicalModel(
            packages=[
                Package(id="p1", name="Root", provenance=prov),
                Package(id="p2", name="Sub", parent_id="p1", provenance=prov),
            ],
            elements=[
                ModelElement(
                    id="e1", kind=ElementKind.CLASS, name="X", package_id="p2", provenance=prov
                )
            ],
        )
        assert len(model.packages) == 2
        assert model.elements[0].package_id == "p2"

    def test_model_with_all_collections(self) -> None:
        prov = _prov()
        model = CanonicalModel(
            packages=[Package(id="p1", name="Root", provenance=prov)],
            elements=[
                ModelElement(
                    id="e1", kind=ElementKind.REQUIREMENT, name="REQ-001", provenance=prov
                )
            ],
            relationships=[],
            diagrams=[ModelDiagram(id="d1", name="D", diagram_type="Logical", provenance=prov)],
            requirement_links=[
                RequirementLink(
                    id="rl1",
                    source_id="e1",
                    target_id="e1",
                    link_type=RequirementLinkType.TRACES,
                    provenance=prov,
                )
            ],
            evidence_links=[
                EvidenceLink(id="ev1", element_id="e1", provenance=prov, excerpt="test")
            ],
            uncertainties=[
                Uncertainty(
                    id="u1",
                    element_id="e1",
                    uncertainty_type=UncertaintyType.EXTRACTION,
                    level=UncertaintyLevel.HIGH,
                    description="low confidence",
                )
            ],
        )
        assert len(model.requirement_links) == 1
        assert len(model.evidence_links) == 1
        assert len(model.uncertainties) == 1
