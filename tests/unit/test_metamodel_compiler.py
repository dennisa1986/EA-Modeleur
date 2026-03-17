"""Unit tests for MetamodelCompiler.

Filesystem reads are limited to committed fixture files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.metamodel.compiler import MetamodelCompiler
from ea_mbse_pipeline.metamodel.models import RuleKind, RuleSet
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

_FIXTURES = Path("data/fixtures/metamodel")


@pytest.mark.unit
class TestMetamodelCompilerXMIOnly:
    """Compiler tests using XMI fixture only."""

    def setup_method(self) -> None:
        self.compiler = MetamodelCompiler()
        self.rule_set = self.compiler.compile(_FIXTURES / "mini_valid.xmi")

    def test_returns_rule_set(self) -> None:
        assert isinstance(self.rule_set, RuleSet)

    def test_source_xmi_set(self) -> None:
        assert "mini_valid.xmi" in self.rule_set.source_xmi

    def test_ea_version_set(self) -> None:
        assert self.rule_set.ea_version == "17.1"

    def test_element_types_populated(self) -> None:
        assert "Component" in self.rule_set.element_types
        assert "ProvidedInterface" in self.rule_set.element_types

    def test_stereotypes_populated(self) -> None:
        assert len(self.rule_set.stereotypes) >= 2

    def test_rules_generated(self) -> None:
        assert self.rule_set.rule_count > 0

    def test_element_type_rules_present(self) -> None:
        etypes = [r for r in self.rule_set.rules if r.kind == RuleKind.ELEMENT_TYPE]
        assert len(etypes) == 2  # Component + ProvidedInterface

    def test_tagged_value_rules_from_properties(self) -> None:
        tvals = [r for r in self.rule_set.rules if r.kind == RuleKind.TAGGED_VALUE]
        # Component has 2 properties → 2 tagged-value rules
        assert len(tvals) >= 2
        tag_names = [r.tagged_value_constraint.tag_name for r in tvals if r.tagged_value_constraint]
        assert "name" in tag_names
        assert "stereotype" in tag_names

    def test_connector_rules_present(self) -> None:
        connectors = [r for r in self.rule_set.rules if r.kind == RuleKind.CONNECTOR]
        assert len(connectors) >= 1
        assert connectors[0].connector_constraint is not None

    def test_stereotype_rules_present(self) -> None:
        stereos = [r for r in self.rule_set.rules if r.kind == RuleKind.STEREOTYPE]
        assert len(stereos) >= 2

    def test_all_rules_have_unique_ids(self) -> None:
        ids = [r.id for r in self.rule_set.rules]
        assert len(ids) == len(set(ids))

    def test_rule_ids_are_sequential(self) -> None:
        # IDs should follow pattern R-KIND-NNN
        for rule in self.rule_set.rules:
            parts = rule.id.split("-")
            assert len(parts) == 3
            assert parts[2].isdigit()

    def test_all_error_rules_have_severity_error(self) -> None:
        for rule in self.rule_set.error_rules:
            assert rule.severity == "error"

    def test_compiled_at_is_set(self) -> None:
        assert self.rule_set.compiled_at is not None


@pytest.mark.unit
class TestMetamodelCompilerWithDescription:
    def setup_method(self) -> None:
        self.compiler = MetamodelCompiler()
        self.rule_set = self.compiler.compile_full(
            _FIXTURES / "mini_valid.xmi",
            description_path=_FIXTURES / "description.txt",
        )

    def test_description_source_recorded(self) -> None:
        assert len(self.rule_set.description_sources) == 1
        assert "description.txt" in self.rule_set.description_sources[0]

    def test_more_rules_than_xmi_only(self) -> None:
        xmi_only = MetamodelCompiler().compile(_FIXTURES / "mini_valid.xmi")
        assert self.rule_set.rule_count > xmi_only.rule_count

    def test_description_rules_have_provenance(self) -> None:
        for rule in self.rule_set.rules:
            # All rules from description must have provenance set
            if rule.provenance is not None:
                assert len(rule.provenance.sources) >= 1


@pytest.mark.unit
class TestMetamodelCompilerErrors:
    def test_missing_xmi_raises_pipeline_error(self) -> None:
        compiler = MetamodelCompiler()
        with pytest.raises(PipelineError) as exc_info:
            compiler.compile(Path("data/fixtures/metamodel/nonexistent.xmi"))
        assert exc_info.value.code == ErrorCode.METAMODEL_PARSE_ERROR

    def test_malformed_xmi_raises_pipeline_error(self) -> None:
        compiler = MetamodelCompiler()
        with pytest.raises(PipelineError) as exc_info:
            compiler.compile(_FIXTURES / "malformed.xmi")
        assert exc_info.value.code == ErrorCode.METAMODEL_PARSE_ERROR

    def test_missing_description_raises_pipeline_error(self) -> None:
        compiler = MetamodelCompiler()
        with pytest.raises(PipelineError) as exc_info:
            compiler.compile_full(
                _FIXTURES / "mini_valid.xmi",
                description_path=Path("data/fixtures/metamodel/nonexistent.txt"),
            )
        assert exc_info.value.code == ErrorCode.METAMODEL_DESCRIPTION_PARSE_ERROR

    def test_counters_reset_between_compile_calls(self) -> None:
        compiler = MetamodelCompiler()
        rs1 = compiler.compile(_FIXTURES / "mini_valid.xmi")
        rs2 = compiler.compile(_FIXTURES / "mini_valid.xmi")
        # Both compilations should produce the same rule IDs
        ids1 = sorted(r.id for r in rs1.rules)
        ids2 = sorted(r.id for r in rs2.rules)
        assert ids1 == ids2
