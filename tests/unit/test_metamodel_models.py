"""Unit tests for metamodel compiler data models."""

import pytest

from ea_mbse_pipeline.metamodel.models import MetamodelRule, RuleSet


@pytest.mark.unit
class TestMetamodelRule:
    def test_default_severity_is_error(self) -> None:
        rule = MetamodelRule(id="R-001", description="test", constraint="$.elements[?]")
        assert rule.severity == "error"

    def test_source_xmi_ref_defaults_empty(self) -> None:
        rule = MetamodelRule(id="R-002", description="x", constraint="y")
        assert rule.source_xmi_ref == ""


@pytest.mark.unit
class TestRuleSet:
    def test_empty_ruleset(self) -> None:
        rs = RuleSet(source_xmi="model.xmi", ea_version="17.1")
        assert rs.rules == []
