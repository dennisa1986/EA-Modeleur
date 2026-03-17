"""Unit tests for DescriptionParser — heuristic and explicit RULE modes.

Sprint 3.1 hardening: explicit RULE[...] directive tests added.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.metamodel.description_parser import (
    DescriptionConstraint,
    DescriptionParseResult,
    DescriptionParser,
)
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

    def _parse_inline(self, text: str) -> DescriptionParseResult:
        """Helper: invoke _parse_text directly to avoid file I/O."""
        parser = DescriptionParser()
        result = DescriptionParseResult(source_path="<inline>")
        parser._parse_text(text, result)  # noqa: SLF001
        return result

    def test_must_line_extracted(self) -> None:
        result = self._parse_inline("An element MUST have a name.")
        assert len(result.constraints) == 1

    def test_shall_not_is_forbidden(self) -> None:
        result = self._parse_inline("Elements SHALL NOT be nameless.")
        assert len(result.constraints) == 1
        assert result.constraints[0].inferred_kind == "forbidden"

    def test_heading_skipped(self) -> None:
        result = self._parse_inline("# Section Title\nNo constraints here.")
        assert len(result.constraints) == 0

    def test_plain_sentence_skipped(self) -> None:
        result = self._parse_inline("This is an informative note.")
        assert len(result.constraints) == 0

    def test_heuristic_is_not_explicit(self) -> None:
        result = self._parse_inline("Component MUST have a name.")
        assert result.constraints[0].is_explicit is False


# ---------------------------------------------------------------------------
# Explicit RULE[...] directive (Sprint 3.1)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDescriptionParserExplicitRule:
    """Tests for the machine-friendly RULE[kind=...,severity=...]: text format."""

    def _parse_inline(self, text: str) -> DescriptionParseResult:
        parser = DescriptionParser()
        result = DescriptionParseResult(source_path="<inline>")
        parser._parse_text(text, result)  # noqa: SLF001
        return result

    def test_explicit_connector_rule_extracted(self) -> None:
        result = self._parse_inline(
            "RULE[kind=connector,severity=error]: Connector must have source and target."
        )
        assert len(result.constraints) == 1
        c = result.constraints[0]
        assert c.inferred_kind == "connector"
        assert c.severity == "error"
        assert c.is_explicit is True
        assert "source and target" in c.raw_text

    def test_explicit_naming_warning(self) -> None:
        result = self._parse_inline("RULE[kind=naming,severity=warning]: Use PascalCase.")
        c = result.constraints[0]
        assert c.inferred_kind == "naming"
        assert c.severity == "warning"
        assert c.is_explicit is True

    def test_explicit_default_severity_is_error(self) -> None:
        result = self._parse_inline("RULE[kind=tagged_value]: Version tag required.")
        assert result.constraints[0].severity == "error"

    def test_explicit_default_kind_is_general(self) -> None:
        result = self._parse_inline("RULE[severity=warning]: Advisory note.")
        assert result.constraints[0].inferred_kind == "general"
        assert result.constraints[0].severity == "warning"

    def test_explicit_empty_attrs_uses_defaults(self) -> None:
        result = self._parse_inline("RULE[]: All elements need a description.")
        c = result.constraints[0]
        assert c.inferred_kind == "general"
        assert c.severity == "error"
        assert c.is_explicit is True

    def test_explicit_no_must_keyword_required(self) -> None:
        """Explicit rules are recognised even without MUST/SHALL."""
        result = self._parse_inline("RULE[kind=connector]: Links need a target.")
        assert len(result.constraints) == 1

    def test_all_valid_kinds_accepted(self) -> None:
        kinds = [
            "connector", "naming", "tagged_value",
            "package_placement", "forbidden", "general",
        ]
        for kind in kinds:
            result = self._parse_inline(f"RULE[kind={kind}]: Test constraint.")
            assert result.constraints[0].inferred_kind == kind, f"kind={kind}"

    def test_unknown_kind_defaults_to_general_with_warning(self) -> None:
        result = self._parse_inline("RULE[kind=bogus]: Some rule.")
        assert result.constraints[0].inferred_kind == "general"
        assert len(result.warnings) == 1
        assert "bogus" in result.warnings[0]

    def test_unknown_severity_defaults_to_error_with_warning(self) -> None:
        result = self._parse_inline("RULE[severity=critical]: Some rule.")
        assert result.constraints[0].severity == "error"
        assert len(result.warnings) == 1
        assert "critical" in result.warnings[0]

    def test_directive_case_insensitive(self) -> None:
        result = self._parse_inline("rule[kind=connector]: Test.")
        assert len(result.constraints) == 1
        assert result.constraints[0].is_explicit is True

    def test_mixed_explicit_and_heuristic(self) -> None:
        text = (
            "RULE[kind=connector,severity=error]: Connector needs target.\n"
            "Element names MUST start with uppercase.\n"
            "This line has no keywords and is skipped.\n"
        )
        result = self._parse_inline(text)
        assert len(result.constraints) == 2
        explicit = [c for c in result.constraints if c.is_explicit]
        heuristic = [c for c in result.constraints if not c.is_explicit]
        assert len(explicit) == 1
        assert len(heuristic) == 1

    def test_section_assigned_to_explicit_rule(self) -> None:
        text = "# Connector Rules\nRULE[kind=connector]: Must have target.\n"
        result = self._parse_inline(text)
        assert result.constraints[0].section == "Connector Rules"

    def test_explicit_fixture_file(self) -> None:
        """Committed fixture with explicit rules compiles without error."""
        result = DescriptionParser().parse(
            Path("data/fixtures/metamodel/description_explicit.txt")
        )
        explicit = [c for c in result.constraints if c.is_explicit]
        heuristic = [c for c in result.constraints if not c.is_explicit]
        # Fixture has 6 RULE[...] lines and 3 MUST/SHALL/FORBIDDEN lines
        assert len(explicit) == 6
        assert len(heuristic) == 3
        kinds = {c.inferred_kind for c in explicit}
        assert {"connector", "naming", "tagged_value", "forbidden", "package_placement", "general"} == kinds
