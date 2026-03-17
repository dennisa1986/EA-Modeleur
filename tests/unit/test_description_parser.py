"""Unit tests for DescriptionParser.

Filesystem reads are limited to committed fixture files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.metamodel.description_parser import DescriptionParser
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

_FIXTURES = Path("data/fixtures/metamodel")


@pytest.mark.unit
class TestDescriptionParserHappyPath:
    def setup_method(self) -> None:
        self.parser = DescriptionParser()
        self.result = self.parser.parse(_FIXTURES / "description.txt")

    def test_source_path_set(self) -> None:
        assert "description.txt" in self.result.source_path

    def test_sections_detected(self) -> None:
        assert "Component Rules" in self.result.sections
        assert "Naming Rules" in self.result.sections

    def test_constraint_count(self) -> None:
        # The fixture has multiple MUST/SHALL/FORBIDDEN lines
        assert len(self.result.constraints) >= 8

    def test_tagged_value_kind_detected(self) -> None:
        tv = [c for c in self.result.constraints if c.inferred_kind == "tagged_value"]
        assert len(tv) >= 1
        assert any("tagged value" in c.raw_text.lower() for c in tv)

    def test_naming_kind_detected(self) -> None:
        naming = [c for c in self.result.constraints if c.inferred_kind == "naming"]
        assert len(naming) >= 1

    def test_package_kind_detected(self) -> None:
        pkg = [c for c in self.result.constraints if c.inferred_kind == "package_placement"]
        assert len(pkg) >= 1

    def test_forbidden_kind_detected(self) -> None:
        forb = [c for c in self.result.constraints if c.inferred_kind == "forbidden"]
        assert len(forb) >= 1

    def test_section_assigned_to_constraint(self) -> None:
        comp_rules = [c for c in self.result.constraints if c.section == "Component Rules"]
        assert len(comp_rules) >= 2

    def test_severity_is_error_for_must(self) -> None:
        must_lines = [c for c in self.result.constraints if "MUST" in c.raw_text.upper()]
        for c in must_lines:
            assert c.severity == "error"

    def test_source_line_is_positive(self) -> None:
        for c in self.result.constraints:
            assert c.source_line > 0


@pytest.mark.unit
class TestDescriptionParserErrors:
    def test_missing_file_raises_pipeline_error(self) -> None:
        parser = DescriptionParser()
        with pytest.raises(PipelineError) as exc_info:
            parser.parse(Path("data/fixtures/metamodel/nonexistent.txt"))
        assert exc_info.value.code == ErrorCode.METAMODEL_DESCRIPTION_PARSE_ERROR

    def test_error_has_path_context(self) -> None:
        parser = DescriptionParser()
        with pytest.raises(PipelineError) as exc_info:
            parser.parse(Path("data/fixtures/metamodel/nonexistent.txt"))
        assert "path" in exc_info.value.context


@pytest.mark.unit
class TestDescriptionParserInline:
    """Tests using inline text (no fixture I/O needed beyond parser construction)."""

    def _parse_text(self, text: str) -> list[object]:
        """Helper: write text to tmp and parse, but inline approach via _parse_text."""
        from ea_mbse_pipeline.metamodel.description_parser import DescriptionParseResult

        parser = DescriptionParser()
        result = DescriptionParseResult(source_path="<inline>")
        parser._parse_text(text, result)  # noqa: SLF001
        return result.constraints  # type: ignore[return-value]

    def test_must_line_extracted(self) -> None:
        constraints = self._parse_text("An element MUST have a name.")
        assert len(constraints) == 1

    def test_shall_not_is_forbidden(self) -> None:
        constraints = self._parse_text("Elements SHALL NOT be nameless.")
        assert len(constraints) == 1
        assert constraints[0].inferred_kind == "forbidden"  # type: ignore[union-attr]

    def test_heading_skipped(self) -> None:
        constraints = self._parse_text("# Section Title\nNo constraints here.")
        assert len(constraints) == 0

    def test_plain_sentence_skipped(self) -> None:
        constraints = self._parse_text("This is an informative note.")
        assert len(constraints) == 0
