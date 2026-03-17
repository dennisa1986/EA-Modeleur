"""Canonical model — the mandatory intermediate representation.

The JSON Schema at schemas/canonical_model.schema.json is authoritative.
These Pydantic models mirror that schema and provide Python-side validation.

All elements must carry a Provenance object.  Elements without provenance
are rejected with ErrorCode.CANONICAL_MISSING_PROVENANCE.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from ea_mbse_pipeline.shared.provenance import Provenance


class ElementKind(StrEnum):
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
    id: str = Field(..., description="Pipeline-internal UUID.")
    ea_guid: str | None = None
    kind: ElementKind
    name: str
    stereotype: str | None = None
    package_path: str = ""
    """Dot-separated EA package path, e.g. 'Root.Domain.Subdomain'."""
    attributes: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    tagged_values: dict[str, str] = {}
    notes: str = ""
    provenance: Provenance


class ModelRelationship(BaseModel):
    id: str
    kind: RelationshipKind
    source_id: str
    target_id: str
    name: str = ""
    stereotype: str | None = None
    tagged_values: dict[str, str] = {}
    provenance: Provenance


class ModelDiagram(BaseModel):
    id: str
    name: str
    diagram_type: str
    """EA diagram type name, e.g. 'Logical', 'Component', 'Use Case'."""
    package_path: str = ""
    element_ids: list[str] = []
    provenance: Provenance


class CanonicalModel(BaseModel):
    """Root of the canonical intermediate model."""

    schema_version: str = "1.0"
    source_description: str = ""
    elements: list[ModelElement] = []
    relationships: list[ModelRelationship] = []
    diagrams: list[ModelDiagram] = []
