"""Metamodel compiler output models.

Sprint 3: enriches MetamodelRule with kind/scope/typed constraint details
and provenance. RuleSet gains element_types, stereotypes, compiled_at.

All Sprint-2 field names are preserved — existing construction sites remain
valid. New fields all carry defaults.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ea_mbse_pipeline.shared.provenance import Provenance


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Rule classification
# ---------------------------------------------------------------------------


class RuleKind(StrEnum):
    """Classifies which aspect of the metamodel a rule governs."""

    ELEMENT_TYPE = "element_type"
    STEREOTYPE = "stereotype"
    CONNECTOR = "connector"
    TAGGED_VALUE = "tagged_value"
    PACKAGE_PLACEMENT = "package_placement"
    NAMING = "naming"
    DIAGRAM = "diagram"
    FORBIDDEN = "forbidden"
    GENERAL = "general"


class RuleScope(StrEnum):
    """The model scope a rule applies to."""

    ELEMENT = "element"
    RELATIONSHIP = "relationship"
    DIAGRAM = "diagram"
    PACKAGE = "package"
    MODEL = "model"


# ---------------------------------------------------------------------------
# Typed constraint detail models
# ---------------------------------------------------------------------------


class ConnectorConstraint(BaseModel):
    """Constraint on allowed (or forbidden) connector types between element types."""

    connector_type: str
    """UML connector type, e.g. 'uml:Association', 'uml:Dependency'."""
    source_types: list[str] = []
    """Allowed source element types. Empty = unrestricted."""
    target_types: list[str] = []
    """Allowed target element types. Empty = unrestricted."""
    allowed: bool = True
    """True = combination is allowed; False = combination is forbidden."""


class TaggedValueConstraint(BaseModel):
    """Constraint on required or restricted tagged values."""

    tag_name: str
    required: bool = True
    value_pattern: str | None = None
    """Optional regex the value must match."""
    applies_to_types: list[str] = []
    """Element types this constraint applies to. Empty = all."""


class NamingConstraint(BaseModel):
    """Naming pattern constraint for element names."""

    pattern: str
    """Regex pattern that element names must match."""
    applies_to_types: list[str] = []
    """Element types this constraint applies to. Empty = all."""
    applies_to_stereotypes: list[str] = []
    """Stereotypes this constraint applies to. Empty = all."""


class PackagePlacementConstraint(BaseModel):
    """Package placement rules for element types."""

    element_types: list[str] = []
    """Element types this rule applies to. Empty = all."""
    allowed_packages: list[str] = []
    """Packages (dot-notation) where these types may reside."""
    forbidden_packages: list[str] = []
    """Packages (dot-notation) where these types may NOT reside."""


class DiagramConstraint(BaseModel):
    """Rules about which element types may appear in which diagram types."""

    diagram_type: str
    allowed_element_types: list[str] = []
    """Explicitly allowed element types. Empty = no restriction."""
    forbidden_element_types: list[str] = []
    """Explicitly forbidden element types."""
    required_element_types: list[str] = []
    """Element types that must appear in this diagram type."""


class ForbiddenPattern(BaseModel):
    """An explicitly forbidden combination of type / stereotype / connector."""

    description: str
    element_types: list[str] = []
    stereotypes: list[str] = []
    connector_types: list[str] = []


# ---------------------------------------------------------------------------
# Core rule and rule set
# ---------------------------------------------------------------------------


class MetamodelRule(BaseModel):
    """A single machine-enforceable rule derived from the XMI metamodel.

    Sprint 3: enriched with ``kind``, ``scope``, typed constraint detail
    models, and ``provenance``. All new fields have defaults so existing
    construction sites (tests, stubs) remain valid.
    """

    id: str
    """Unique rule identifier, e.g. 'R-CONN-001'."""

    # Classification (Sprint 3)
    kind: RuleKind = RuleKind.GENERAL
    scope: RuleScope = RuleScope.ELEMENT

    description: str
    constraint: str = ""
    """JSON-Path, OCL expression, or structured constraint string."""
    severity: str = "error"
    """'error' halts the pipeline; 'warning' is recorded but does not halt."""
    source_xmi_ref: str = ""
    """XPath within the source XMI where this rule originates."""

    provenance: Provenance | None = None
    """Provenance of this rule. The compiler always sets this;
    None is only valid for manually constructed stubs/tests."""

    # Typed constraint details (Sprint 3) — mutually optional
    connector_constraint: ConnectorConstraint | None = None
    tagged_value_constraint: TaggedValueConstraint | None = None
    naming_constraint: NamingConstraint | None = None
    package_placement: PackagePlacementConstraint | None = None
    diagram_constraint: DiagramConstraint | None = None
    forbidden_pattern: ForbiddenPattern | None = None


class RuleSet(BaseModel):
    """Full compiled rule set from one XMI metamodel file.

    Sprint 3: extended with ``element_types``, ``stereotypes``,
    ``compiled_at``, and ``description_sources``.
    """

    source_xmi: str
    """Repo-relative or absolute path to the source XMI file."""
    ea_version: str
    """EA version this rule set targets, e.g. '17.1'."""

    rules: list[MetamodelRule] = []

    # Registry-level summaries (Sprint 3)
    element_types: list[str] = []
    """All element type names discovered in the XMI."""
    stereotypes: list[str] = []
    """All stereotype names discovered in the XMI."""
    compiled_at: datetime = Field(default_factory=_utcnow)
    """Timestamp when this rule set was compiled."""
    description_sources: list[str] = []
    """Paths to supplementary description files that contributed rules."""

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    @property
    def error_rules(self) -> list[MetamodelRule]:
        return [r for r in self.rules if r.severity == "error"]

    @property
    def warning_rules(self) -> list[MetamodelRule]:
        return [r for r in self.rules if r.severity == "warning"]
