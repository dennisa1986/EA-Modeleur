"""Unit tests for XMIParser.

All tests use in-memory fixture paths; no network I/O.
Filesystem access is limited to reading committed fixture files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.metamodel.xmi_parser import XMIParser
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

# Fixture directory — committed to the repo, treated as read-only by tests
_FIXTURES = Path("data/fixtures/metamodel")


@pytest.mark.unit
class TestXMIParserValidFile:
    """Happy-path tests against mini_valid.xmi."""

    def setup_method(self) -> None:
        self.parser = XMIParser()
        self.result = self.parser.parse(_FIXTURES / "mini_valid.xmi")

    def test_source_path_is_set(self) -> None:
        assert "mini_valid.xmi" in self.result.source_path

    def test_ea_version_extracted(self) -> None:
        assert self.result.ea_version == "17.1"

    def test_classes_found(self) -> None:
        names = [c.name for c in self.result.classes]
        assert "Component" in names
        assert "ProvidedInterface" in names

    def test_class_xmi_type_preserved(self) -> None:
        component = next(c for c in self.result.classes if c.name == "Component")
        assert component.xmi_type == "uml:Class"

    def test_interface_xmi_type(self) -> None:
        iface = next(c for c in self.result.classes if c.name == "ProvidedInterface")
        assert iface.xmi_type == "uml:Interface"

    def test_properties_on_component(self) -> None:
        component = next(c for c in self.result.classes if c.name == "Component")
        prop_names = [p.name for p in component.properties]
        assert "name" in prop_names
        assert "stereotype" in prop_names

    def test_connector_found(self) -> None:
        assert len(self.result.connectors) == 1
        conn = self.result.connectors[0]
        assert conn.name == "realizes"
        assert conn.connector_type == "uml:Association"

    def test_package_found(self) -> None:
        pkg_names = [p.name for p in self.result.packages]
        assert "Architecture" in pkg_names or "EA_Model" in pkg_names

    def test_stereotypes_from_extension(self) -> None:
        names = [s.name for s in self.result.stereotypes]
        assert "component" in names
        assert "interface" in names

    def test_xmi_ref_set_on_classes(self) -> None:
        for cls in self.result.classes:
            assert cls.xmi_ref != ""


@pytest.mark.unit
class TestXMIParserIncompleteFile:
    """Parser should handle incomplete/degenerate XMI gracefully."""

    def setup_method(self) -> None:
        self.parser = XMIParser()
        self.result = self.parser.parse(_FIXTURES / "incomplete.xmi")

    def test_only_named_class_extracted(self) -> None:
        # "OrphanClass" has no xmi:id (skipped by package parser but may appear in classes)
        # "NoName" has no name → skipped with warning
        # "ValidClass" → must appear
        names = [c.name for c in self.result.classes]
        assert "ValidClass" in names

    def test_unnamed_class_skipped_with_warning(self) -> None:
        # The class with xmi:id but no name should produce a warning
        assert any("unnamed" in w.lower() or "_cls_noname" in w for w in self.result.warnings)

    def test_no_connectors(self) -> None:
        assert self.result.connectors == []


@pytest.mark.unit
class TestXMIParserErrors:
    """Error handling tests."""

    def test_missing_file_raises_pipeline_error(self) -> None:
        parser = XMIParser()
        with pytest.raises(PipelineError) as exc_info:
            parser.parse(Path("data/fixtures/metamodel/nonexistent.xmi"))
        assert exc_info.value.code == ErrorCode.METAMODEL_PARSE_ERROR

    def test_malformed_xml_raises_pipeline_error(self) -> None:
        parser = XMIParser()
        with pytest.raises(PipelineError) as exc_info:
            parser.parse(_FIXTURES / "malformed.xmi")
        assert exc_info.value.code == ErrorCode.METAMODEL_PARSE_ERROR

    def test_pipeline_error_has_path_context(self) -> None:
        parser = XMIParser()
        with pytest.raises(PipelineError) as exc_info:
            parser.parse(Path("data/fixtures/metamodel/nonexistent.xmi"))
        assert "path" in exc_info.value.context
