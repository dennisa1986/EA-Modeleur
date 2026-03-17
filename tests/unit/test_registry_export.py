"""Unit tests for RegistryExporter.

Content-building tests (build_markdown, model_dump) run without filesystem I/O.
File-writing tests are marked @pytest.mark.integration and use tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ea_mbse_pipeline.metamodel.models import (
    ConnectorConstraint,
    MetamodelRule,
    RuleKind,
    RuleScope,
    RuleSet,
    TaggedValueConstraint,
)
from ea_mbse_pipeline.metamodel.registry_export import RegistryExporter
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError


def _make_rule_set() -> RuleSet:
    return RuleSet(
        source_xmi="data/raw/metamodel/model.xmi",
        ea_version="17.1",
        element_types=["Component", "Interface"],
        stereotypes=["component"],
        rules=[
            MetamodelRule(
                id="R-ETYPE-001",
                kind=RuleKind.ELEMENT_TYPE,
                scope=RuleScope.ELEMENT,
                description="Component is defined.",
                constraint="element.type == 'Component'",
                severity="error",
            ),
            MetamodelRule(
                id="R-CONN-001",
                kind=RuleKind.CONNECTOR,
                scope=RuleScope.RELATIONSHIP,
                description="Realizes connector allowed.",
                severity="error",
                connector_constraint=ConnectorConstraint(
                    connector_type="uml:Association",
                    source_types=["Component"],
                    target_types=["Interface"],
                ),
            ),
            MetamodelRule(
                id="R-TVAL-001",
                kind=RuleKind.TAGGED_VALUE,
                scope=RuleScope.ELEMENT,
                description="Component must have 'name' tagged value.",
                severity="error",
                tagged_value_constraint=TaggedValueConstraint(
                    tag_name="name",
                    required=True,
                    applies_to_types=["Component"],
                ),
            ),
        ],
    )


@pytest.mark.unit
class TestRegistryExporterMarkdown:
    def setup_method(self) -> None:
        self.exporter = RegistryExporter()
        self.rule_set = _make_rule_set()
        self.md = self.exporter.build_markdown(self.rule_set)

    def test_title_present(self) -> None:
        assert "# Metamodel Constraint Registry" in self.md

    def test_source_xmi_in_output(self) -> None:
        assert "data/raw/metamodel/model.xmi" in self.md

    def test_ea_version_in_output(self) -> None:
        assert "17.1" in self.md

    def test_element_types_section(self) -> None:
        assert "## Element Types" in self.md
        assert "`Component`" in self.md
        assert "`Interface`" in self.md

    def test_stereotypes_section(self) -> None:
        assert "## Stereotypes" in self.md
        assert "`component`" in self.md

    def test_rule_table_present(self) -> None:
        # Rules are grouped by kind; at least one kind section must appear
        assert "## Rules:" in self.md

    def test_all_rule_ids_present(self) -> None:
        assert "`R-ETYPE-001`" in self.md
        assert "`R-CONN-001`" in self.md
        assert "`R-TVAL-001`" in self.md

    def test_connector_detail_block(self) -> None:
        assert "uml:Association" in self.md

    def test_tagged_value_detail_block(self) -> None:
        assert "tag_name" in self.md or "Tagged value" in self.md


@pytest.mark.unit
class TestRegistryExporterJSON:
    def test_model_dump_roundtrip(self) -> None:
        rule_set = _make_rule_set()
        payload = rule_set.model_dump(mode="json")
        # Verify required top-level keys
        assert payload["source_xmi"] == "data/raw/metamodel/model.xmi"
        assert payload["ea_version"] == "17.1"
        assert len(payload["rules"]) == 3

    def test_rule_kind_serialised_as_string(self) -> None:
        rule_set = _make_rule_set()
        payload = rule_set.model_dump(mode="json")
        kinds = [r["kind"] for r in payload["rules"]]
        assert "element_type" in kinds
        assert "connector" in kinds

    def test_json_is_valid_json_string(self) -> None:
        rule_set = _make_rule_set()
        payload = rule_set.model_dump(mode="json")
        text = json.dumps(payload, indent=2)
        # Must round-trip through json.loads without error
        parsed = json.loads(text)
        assert parsed["ea_version"] == "17.1"


@pytest.mark.integration
class TestRegistryExporterFileIO:
    """File I/O integration tests — use tmp_path."""

    def test_export_json_writes_file(self, tmp_path: Path) -> None:
        exporter = RegistryExporter()
        rule_set = _make_rule_set()
        out = tmp_path / "registry.json"
        result = exporter.export_json(rule_set, out)
        assert result == out
        assert out.exists()
        loaded = json.loads(out.read_text())
        assert loaded["ea_version"] == "17.1"
        assert len(loaded["rules"]) == 3

    def test_export_markdown_writes_file(self, tmp_path: Path) -> None:
        exporter = RegistryExporter()
        rule_set = _make_rule_set()
        out = tmp_path / "report.md"
        result = exporter.export_markdown(rule_set, out)
        assert result == out
        assert out.exists()
        content = out.read_text()
        assert "# Metamodel Constraint Registry" in content

    def test_export_json_creates_parent_dirs(self, tmp_path: Path) -> None:
        exporter = RegistryExporter()
        rule_set = _make_rule_set()
        out = tmp_path / "subdir" / "deep" / "registry.json"
        exporter.export_json(rule_set, out)
        assert out.exists()

    def test_export_json_raises_on_write_failure(self, tmp_path: Path) -> None:
        exporter = RegistryExporter()
        rule_set = _make_rule_set()
        # Use a path that is a directory, not a file — should cause OSError
        bad_path = tmp_path  # tmp_path itself is a directory
        with pytest.raises(PipelineError) as exc_info:
            exporter.export_json(rule_set, bad_path)
        assert exc_info.value.code == ErrorCode.METAMODEL_REGISTRY_EXPORT_FAIL
