"""Shared pytest fixtures for ea_mbse_pipeline tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.canonical.models import CanonicalModel, ElementKind, ModelElement
from ea_mbse_pipeline.metamodel.models import RuleSet
from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef

DATA_FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"
DATA_GOLDEN   = Path(__file__).parent.parent / "data" / "golden"


def _test_provenance(file: str = "test.txt") -> Provenance:
    return Provenance(
        sources=[SourceRef(file_path=file)],
        derivation_method="test-fixture",
    )


@pytest.fixture()
def test_provenance() -> Provenance:
    return _test_provenance()


@pytest.fixture()
def minimal_canonical_model() -> CanonicalModel:
    """A minimal valid CanonicalModel with a single element and provenance."""
    return CanonicalModel(
        source_description="test",
        elements=[
            ModelElement(
                id="elem-001",
                kind=ElementKind.CLASS,
                name="ExampleClass",
                provenance=_test_provenance(),
            )
        ],
    )


@pytest.fixture()
def empty_ruleset() -> RuleSet:
    return RuleSet(source_xmi="test.xmi", ea_version="17.1")
