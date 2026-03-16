"""Data models for import validation output."""

from __future__ import annotations

from pydantic import BaseModel


class ImportIssue(BaseModel):
    xpath: str | None = None
    """XPath within the serialized XMI where the issue was detected."""
    message: str
    severity: str = "error"


class ImportReport(BaseModel):
    importable: bool
    """True if the artefact passed all import-readiness checks."""
    issues: list[ImportIssue] = []
