"""Stage 3 — Canonical Model.

Holds the mandatory language-neutral JSON intermediate representation.
The JSON Schema at ``schemas/canonical_model.schema.json`` is authoritative.
This stage MUST be traversed by every pipeline run — no shortcut paths.

Public API
----------
Import the models, builder, and I/O helpers directly from this package::

    from ea_mbse_pipeline.canonical import (
        CanonicalModel, ModelElement, ModelRelationship, Package,
        ModelDiagram, DiagramObject, ElementBounds,
        EvidenceLink, Uncertainty, UncertaintyLevel, UncertaintyType,
        RequirementLink, RequirementLinkType,
        ElementKind, RelationshipKind, Visibility, ParameterDirection,
        TaggedValue, Attribute, Operation, Parameter,
        CanonicalModelBuilder,
        load_canonical_model, save_canonical_model, validate_against_schema,
        new_id, to_ea_guid, from_ea_guid,
    )
"""

from ea_mbse_pipeline.canonical.builders import CanonicalModelBuilder
from ea_mbse_pipeline.canonical.diagram_models import (
    DiagramObject,
    ElementBounds,
    ModelDiagram,
)
from ea_mbse_pipeline.canonical.evidence_models import EvidenceLink
from ea_mbse_pipeline.canonical.ids import from_ea_guid, new_id, to_ea_guid
from ea_mbse_pipeline.canonical.io import (
    load_canonical_model,
    save_canonical_model,
    validate_against_schema,
)
from ea_mbse_pipeline.canonical.models import (
    Attribute,
    CanonicalModel,
    ElementKind,
    ModelElement,
    ModelRelationship,
    Operation,
    Package,
    Parameter,
    ParameterDirection,
    RelationshipKind,
    RequirementLink,
    RequirementLinkType,
    TaggedValue,
    Visibility,
)
from ea_mbse_pipeline.canonical.uncertainty_models import (
    Uncertainty,
    UncertaintyLevel,
    UncertaintyType,
)

__all__ = [
    # Root container
    "CanonicalModel",
    # First-class artefacts
    "Package",
    "ModelElement",
    "ModelRelationship",
    "RequirementLink",
    # Diagram
    "ModelDiagram",
    "DiagramObject",
    "ElementBounds",
    # Evidence & uncertainty
    "EvidenceLink",
    "Uncertainty",
    "UncertaintyLevel",
    "UncertaintyType",
    # Enumerations
    "ElementKind",
    "RelationshipKind",
    "RequirementLinkType",
    "Visibility",
    "ParameterDirection",
    # Value objects / sub-elements
    "TaggedValue",
    "Attribute",
    "Operation",
    "Parameter",
    # Builder
    "CanonicalModelBuilder",
    # I/O
    "load_canonical_model",
    "save_canonical_model",
    "validate_against_schema",
    # ID utilities
    "new_id",
    "to_ea_guid",
    "from_ea_guid",
]
