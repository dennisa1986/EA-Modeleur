"""Data models for compiled metamodel artefacts."""

from __future__ import annotations

from pydantic import BaseModel


class MetamodelRule(BaseModel):
    """A single machine-enforceable rule derived from the XMI metamodel."""

    id: str
    """Unique rule identifier, e.g. 'R-COMP-001'."""
    description: str
    constraint: str
    """OCL or JSON-Path expression that can be evaluated against the canonical model."""
    severity: str = "error"
    """'error' halts the pipeline; 'warning' is reported but does not halt."""


class RuleSet(BaseModel):
    """Full set of rules compiled from one metamodel XMI file."""

    source_xmi: str
    ea_version: str
    rules: list[MetamodelRule] = []
