"""Unit tests for canonical model data models."""

import pytest

from ea_mbse_pipeline.canonical.models import (
    CanonicalModel,
    ElementKind,
    ModelElement,
    ModelRelationship,
    RelationshipKind,
)
from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef


def _prov() -> Provenance:
    return Provenance(sources=[SourceRef(file_path="test.txt")], derivation_method="test")


@pytest.mark.unit
class TestModelElement:
    def test_element_requires_provenance(self) -> None:
        elem = ModelElement(id="e1", kind=ElementKind.CLASS, name="Foo", provenance=_prov())
        assert elem.provenance.derivation_method == "test"

    def test_defaults(self) -> None:
        elem = ModelElement(id="e1", kind=ElementKind.COMPONENT, name="C", provenance=_prov())
        assert elem.attributes == []
        assert elem.stereotype is None
        assert elem.package_path == ""


@pytest.mark.unit
class TestCanonicalModel:
    def test_empty_model(self) -> None:
        model = CanonicalModel()
        assert model.elements == []
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
