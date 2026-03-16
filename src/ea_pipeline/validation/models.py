"""Data models for validation output."""

from __future__ import annotations

from pydantic import BaseModel


class ValidationFinding(BaseModel):
    rule_id: str
    severity: str
    """'error' or 'warning'."""
    element_id: str | None = None
    message: str


class ValidationReport(BaseModel):
    passed: bool
    """True only if there are zero 'error' findings."""
    findings: list[ValidationFinding] = []

    @property
    def errors(self) -> list[ValidationFinding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[ValidationFinding]:
        return [f for f in self.findings if f.severity == "warning"]
