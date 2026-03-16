"""Unit tests for validation data models."""

import pytest

from ea_mbse_pipeline.validation.models import ValidationFinding, ValidationReport


@pytest.mark.unit
class TestValidationReport:
    def test_no_findings_passes(self) -> None:
        report = ValidationReport(passed=True)
        assert report.errors == []
        assert report.warnings == []

    def test_severity_split(self) -> None:
        report = ValidationReport(
            passed=False,
            findings=[
                ValidationFinding(rule_id="R-001", severity="error", message="fail"),
                ValidationFinding(rule_id="R-002", severity="warning", message="warn"),
            ],
        )
        assert len(report.errors) == 1
        assert len(report.warnings) == 1
        assert report.passed is False
