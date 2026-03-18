"""Diagram-specific models for the canonical layer.

Kept in a separate module so ``models.py`` stays manageable and downstream
stages can import only what they need.

``ModelDiagram`` is the canonical representation of an EA diagram.
It holds ``DiagramObject`` entries — one per element placed on the diagram —
each with an optional ``ElementBounds`` layout hint for the serializer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ea_mbse_pipeline.shared.provenance import Provenance


class ElementBounds(BaseModel):
    """Optional 2-D layout hint for a diagram element.

    Coordinates are in EA's internal pixel coordinate system (origin top-left).
    The serializer uses these values when present; they are ignored by all
    other pipeline stages.  Omit them for auto-layout.
    """

    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 60


class DiagramObject(BaseModel):
    """One element placed on a ``ModelDiagram``.

    Links a canonical artefact (``ModelElement`` or ``Package``) to a diagram
    by ``element_id``, with an optional ``bounds`` hint for the serializer.
    """

    id: str = Field(..., description="Pipeline-internal UUID for this placement record.")
    element_id: str = Field(..., description="Ref to ModelElement.id or Package.id.")
    bounds: ElementBounds | None = None


class ModelDiagram(BaseModel):
    """A named EA diagram with typed element placements and mandatory provenance."""

    id: str = Field(..., description="Pipeline-internal UUID.")
    name: str
    diagram_type: str = Field(
        ...,
        description="EA diagram type name, e.g. 'Logical', 'Component', 'Use Case'.",
    )
    package_id: str | None = Field(
        default=None,
        description="Ref to Package.id; None means the diagram lives at the model root.",
    )
    objects: list[DiagramObject] = Field(
        default_factory=list,
        description="Ordered list of element placements on this diagram.",
    )
    provenance: Provenance
