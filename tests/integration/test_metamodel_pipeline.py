"""Integration tests for the full metamodel compilation pipeline.

Tests compile XMI + description → export JSON + Markdown → verify output.
Uses tmp_path for all file output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ea_mbse_pipeline.metamodel.compiler import MetamodelCompiler
from ea_mbse_pipeline.metamodel.rule_registry import RuleRegistry

_FIXTURES = Path("data/fixtures/metamodel")


@pytest.mark.integration
class TestMetamodelPipelineEndToEnd:
    def test_compile_and_export_produces_json_and_markdown(self, tmp_path: Path) -> None:
        compiler = MetamodelCompiler()
        rule_set, json_path, md_path = compiler.compile_and_export(
            _FIXTURES / "mini_valid.xmi",
            output_dir=tmp_path,
        )
        assert json_path.exists()
        assert md_path.exists()
        assert json_path.suffix == ".json"
        assert md_path.suffix == ".md"

    def test_json_output_is_valid_and_complete(self, tmp_path: Path) -> None:
        compiler = MetamodelCompiler()
        rule_set, json_path, _ = compiler.compile_and_export(
            _FIXTURES / "mini_valid.xmi",
            output_dir=tmp_path,
        )
        loaded = json.loads(json_path.read_text())
        assert loaded["ea_version"] == "17.1"
        assert len(loaded["rules"]) == rule_set.rule_count
        assert "Component" in loaded["element_types"]

    def test_markdown_output_is_human_readable(self, tmp_path: Path) -> None:
        compiler = MetamodelCompiler()
        _, _, md_path = compiler.compile_and_export(
            _FIXTURES / "mini_valid.xmi",
            output_dir=tmp_path,
        )
        content = md_path.read_text()
        assert "# Metamodel Constraint Registry" in content
        assert "Component" in content
        assert "|" in content  # rule table

    def test_compile_with_description_adds_rules(self, tmp_path: Path) -> None:
        compiler = MetamodelCompiler()
        rule_set, json_path, md_path = compiler.compile_and_export(
            _FIXTURES / "mini_valid.xmi",
            description_path=_FIXTURES / "description.txt",
            output_dir=tmp_path,
        )
        loaded = json.loads(json_path.read_text())
        # With description, more rules than without
        assert len(loaded["rules"]) > 5
        assert len(loaded["description_sources"]) == 1

    def test_registry_roundtrip_from_json(self, tmp_path: Path) -> None:
        """RuleSet written to JSON must survive a load → RuleRegistry roundtrip."""
        from ea_mbse_pipeline.metamodel.models import RuleSet

        compiler = MetamodelCompiler()
        original_rs, json_path, _ = compiler.compile_and_export(
            _FIXTURES / "mini_valid.xmi",
            output_dir=tmp_path,
        )

        # Re-load from JSON
        loaded_dict = json.loads(json_path.read_text())
        restored_rs = RuleSet.model_validate(loaded_dict)
        registry = RuleRegistry.from_rule_set(restored_rs)

        assert len(registry) == original_rs.rule_count

    def test_output_filenames_derived_from_xmi_stem(self, tmp_path: Path) -> None:
        compiler = MetamodelCompiler()
        _, json_path, md_path = compiler.compile_and_export(
            _FIXTURES / "mini_valid.xmi",
            output_dir=tmp_path,
        )
        assert json_path.name == "mini_valid_registry.json"
        assert md_path.name == "mini_valid_report.md"

    def test_incomplete_xmi_compiles_without_crash(self, tmp_path: Path) -> None:
        """incomplete.xmi is valid XML; compiler must not raise."""
        compiler = MetamodelCompiler()
        rule_set = compiler.compile(_FIXTURES / "incomplete.xmi")
        # Should compile with at least the one valid class
        assert rule_set.rule_count >= 1
        assert "ValidClass" in rule_set.element_types
