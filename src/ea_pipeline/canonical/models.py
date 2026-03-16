"""Canonical model — the language-neutral intermediate representation.

The JSON Schema at schemas/canonical_model.schema.json is authoritative.
These Pydantic models mirror that schema and provide Python-side validation.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ElementKind(StrEnum):
    """EA metaclass kinds supported by the pipeline."""

    CLASS = "Class"
    COMPONENT = "Component"
    ACTOR = "Actor"
    USE_CASE = "UseCase"
    INTERFACE = "Interface"
    NODE = "Node"
    ARTIFACT = "Artifact"
    PACKAGE = "Package"


class RelationshipKind(StrEnum):
    ASSOCIATION = "Association"
    DEPENDENCY = "Dependency"
    REALIZATION = "Realization"
    GENERALIZATION = "Generalization"
    AGGREGATION = "Aggregation"
    COMPOSITION = "Composition"
    FLOW = "Flow"


class ModelElement(BaseModel):
    """A single EA model element."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    ea_guid: str | None = None
    """EA GUID if already assigned (e.g. when updating an existing model)."""
    kind: ElementKind
    name: str
    stereotype: str | None = None
    package_path: str = ""
    """Dot-separated package path, e.g. 'Root.Domain.Subdomain'."""
    attributes: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    tagged_values: dict[str, str] = {}
    notes: str = ""


class ModelRelationship(BaseModel):
    """A directed relationship between two elements."""

    id: str
    kind: RelationshipKind
    source_id: str
    target_id: str
    name: str = ""
    stereotype: str | None = None
    tagged_values: dict[str, str] = {}


class ModelDiagram(BaseModel):
    """A diagram that references model elements."""

    id: str
    name: str
    diagram_type: str
    """EA diagram type name, e.g. 'Logical', 'Component', 'Use Case'."""
    package_path: str = ""
    element_ids: list[str] = []


class CanonicalModel(BaseModel):
    """Root of the canonical intermediate model."""

    schema_version: str = "1.0"
    source_description: str = ""
    elements: list[ModelElement] = []
    relationships: list[ModelRelationship] = []
    diagrams: list[ModelDiagram] = []
