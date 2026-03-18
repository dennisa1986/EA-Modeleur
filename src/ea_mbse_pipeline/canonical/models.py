"""Canonical model — the mandatory intermediate representation.

The JSON Schema at ``schemas/canonical_model.schema.json`` is authoritative.
These Pydantic models mirror that schema exactly and provide Python-side
validation.

All first-class canonical artefacts (``Package``, ``ModelElement``,
``ModelRelationship``, ``ModelDiagram``, ``RequirementLink``,
``EvidenceLink``) must carry a ``Provenance`` object.  Artefacts without
provenance are rejected with ``ErrorCode.CANONICAL_MISSING_PROVENANCE``.

Module layout
-------------
models.py               — core artefacts (Package, Element, Relationship, …)
diagram_models.py       — ModelDiagram, DiagramObject, ElementBounds
evidence_models.py      — EvidenceLink
uncertainty_models.py   — Uncertainty, UncertaintyLevel, UncertaintyType
ids.py                  — ID generation and EA GUID conversion utilities
builders.py             — CanonicalModelBuilder fluent API
io.py                   — JSON load / save with schema validation
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from ea_mbse_pipeline.canonical.diagram_models import (
    DiagramObject,
    ElementBounds,
    ModelDiagram,
)
from ea_mbse_pipeline.canonical.evidence_models import EvidenceLink
from ea_mbse_pipeline.canonical.uncertainty_models import (
    Uncertainty,
    UncertaintyLevel,
    UncertaintyType,
)
from ea_mbse_pipeline.shared.provenance import Provenance

# Re-export sub-module types so callers can do ``from canonical.models import …``
__all__ = [
    # Enumerations
    "ElementKind",
    "RelationshipKind",
    "RequirementLinkType",
    "Visibility",
    "ParameterDirection",
    # Value objects
    "TaggedValue",
    "Parameter",
    # Sub-element models
    "Attribute",
    "Operation",
    # First-class artefacts
    "Package",
    "ModelElement",
    "ModelRelationship",
    "RequirementLink",
    # Diagram models (re-exported for convenience)
    "ElementBounds",
    "DiagramObject",
    "ModelDiagram",
    # Evidence & uncertainty (re-exported for convenience)
    "EvidenceLink",
    "Uncertainty",
    "UncertaintyLevel",
    "UncertaintyType",
    # Root container
    "CanonicalModel",
]


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ElementKind(StrEnum):
    CLASS = "Class"
    COMPONENT = "Component"
    ACTOR = "Actor"
    USE_CASE = "UseCase"
    INTERFACE = "Interface"
    NODE = "Node"
    ARTIFACT = "Artifact"
    PACKAGE = "Package"
    REQUIREMENT = "Requirement"
    BLOCK = "Block"
    ACTIVITY = "Activity"
    STATE = "State"


class RelationshipKind(StrEnum):
    ASSOCIATION = "Association"
    DEPENDENCY = "Dependency"
    REALIZATION = "Realization"
    GENERALIZATION = "Generalization"
    AGGREGATION = "Aggregation"
    COMPOSITION = "Composition"
    FLOW = "Flow"
    TRACE = "Trace"
    REFINE = "Refine"
    DERIVE = "Derive"
    SATISFY = "Satisfy"
    VERIFY = "Verify"


class Visibility(StrEnum):
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    PACKAGE = "package"


class ParameterDirection(StrEnum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"
    RETURN = "return"


class RequirementLinkType(StrEnum):
    DERIVES = "derives"
    SATISFIES = "satisfies"
    VERIFIES = "verifies"
    REFINES = "refines"
    TRACES = "traces"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class TaggedValue(BaseModel):
    """A name-value pair attached to a model element or relationship."""

    name: str
    value: str
    notes: str = ""


class Parameter(BaseModel):
    """A single parameter of an ``Operation``."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    name: str
    type_name: str | None = None
    direction: ParameterDirection = ParameterDirection.IN
    default_value: str | None = None


# ---------------------------------------------------------------------------
# Sub-element models
# ---------------------------------------------------------------------------


class Attribute(BaseModel):
    """A typed attribute (property) of a ``ModelElement``."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    name: str
    type_name: str | None = None
    visibility: Visibility = Visibility.PUBLIC
    initial_value: str | None = None
    tagged_values: list[TaggedValue] = Field(default_factory=list)
    notes: str = ""


class Operation(BaseModel):
    """A named operation / method of a ``ModelElement``."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    name: str
    return_type: str | None = None
    visibility: Visibility = Visibility.PUBLIC
    parameters: list[Parameter] = Field(default_factory=list)
    tagged_values: list[TaggedValue] = Field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# First-class canonical artefacts
# ---------------------------------------------------------------------------


class Package(BaseModel):
    """A package in the EA model hierarchy.

    ``parent_id`` forms a tree structure: ``None`` marks a root package.
    ``path`` is a derived dot-separated string (e.g. ``'Root.Domain.Sub'``);
    the serializer recomputes it from the parent chain — treat it as a hint,
    not a primary key.
    """

    id: str = Field(..., description="Pipeline-internal UUID.")
    name: str
    parent_id: str | None = Field(
        default=None,
        description="Ref to parent Package.id; None means this is a root package.",
    )
    path: str = Field(
        default="",
        description="Dot-separated canonical path derived from the parent chain.",
    )
    stereotype: str | None = None
    tagged_values: list[TaggedValue] = Field(default_factory=list)
    notes: str = ""
    provenance: Provenance


class ModelElement(BaseModel):
    """A first-class UML/SysML element in the canonical model."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    ea_guid: str | None = Field(
        default=None,
        description="Non-None only when ingesting a pre-existing EA export.",
    )
    kind: ElementKind
    name: str
    stereotype: str | None = None
    package_id: str | None = Field(
        default=None,
        description="Ref to Package.id; None means the element is at the model root.",
    )
    attributes: list[Attribute] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)
    tagged_values: list[TaggedValue] = Field(default_factory=list)
    notes: str = ""
    provenance: Provenance


class ModelRelationship(BaseModel):
    """A directed relationship between two canonical artefacts."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    kind: RelationshipKind
    source_id: str = Field(..., description="Ref to ModelElement.id.")
    target_id: str = Field(..., description="Ref to ModelElement.id.")
    name: str = ""
    stereotype: str | None = None
    tagged_values: list[TaggedValue] = Field(default_factory=list)
    provenance: Provenance


class RequirementLink(BaseModel):
    """A typed SysML/MBSE traceability link between canonical artefacts.

    Both ``source_id`` and ``target_id`` may reference any artefact that
    carries an ``id`` field.
    """

    id: str = Field(..., description="Pipeline-internal UUID.")
    source_id: str
    target_id: str
    link_type: RequirementLinkType
    notes: str = ""
    provenance: Provenance


# ---------------------------------------------------------------------------
# Root container
# ---------------------------------------------------------------------------


class CanonicalModel(BaseModel):
    """Root of the canonical intermediate model.

    All list fields default to empty so that callers can construct partial
    models incrementally (e.g. via ``CanonicalModelBuilder``).  Call
    ``io.save_canonical_model`` to persist and validate against the schema.
    """

    schema_version: str = "1.0"
    source_description: str = ""
    packages: list[Package] = Field(default_factory=list)
    elements: list[ModelElement] = Field(default_factory=list)
    relationships: list[ModelRelationship] = Field(default_factory=list)
    diagrams: list[ModelDiagram] = Field(default_factory=list)
    requirement_links: list[RequirementLink] = Field(default_factory=list)
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)
