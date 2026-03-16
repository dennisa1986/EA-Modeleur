"""EA Test stage output models."""

from __future__ import annotations

from pydantic import BaseModel


class EATestIssue(BaseModel):
    xpath: str | None = None
    """XPath within the serialised XMI where the issue was found."""
    message: str
    severity: str = "error"   # 'error' | 'warning'


class EATestReport(BaseModel):
    importable: bool
    """True if the artefact passed all import-readiness checks."""
    golden_match: bool | None = None
    """True/False if a golden file was compared; None if no golden exists yet."""
    issues: list[EATestIssue] = []
