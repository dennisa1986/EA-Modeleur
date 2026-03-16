"""Metamodel compiler output models."""

from __future__ import annotations

from pydantic import BaseModel


class MetamodelRule(BaseModel):
    """A single machine-enforceable rule derived from the XMI metamodel."""

    id: str
    """Unique rule identifier, e.g. 'R-COMP-001'."""
    description: str
    constraint: str
    """JSON-Path or OCL expression evaluable against a CanonicalModel."""
    severity: str = "error"
    """'error' halts the pipeline; 'warning' is recorded but does not halt."""
    source_xmi_ref: str = ""
    """XPath within the source XMI where this rule originates."""


class RuleSet(BaseModel):
    """Full compiled rule set from one XMI metamodel file."""

    source_xmi: str
    ea_version: str
    rules: list[MetamodelRule] = []
