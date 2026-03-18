"""Fluent builder API for constructing ``CanonicalModel`` instances.

Usage example::

    from ea_mbse_pipeline.canonical.builders import CanonicalModelBuilder
    from ea_mbse_pipeline.canonical.ids import new_id
    from ea_mbse_pipeline.canonical.models import (
        ElementKind, RelationshipKind, RequirementLinkType, TaggedValue,
    )
    from ea_mbse_pipeline.canonical.uncertainty_models import (
        UncertaintyLevel, UncertaintyType,
    )
    from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef

    prov = Provenance(
        sources=[SourceRef(file_path="data/raw/corpus/spec.pdf", page=12)],
        derivation_method="text-extraction",
    )

    pkg_id = new_id()
    sensor_id = new_id()
    collector_id = new_id()

    model = (
        CanonicalModelBuilder(source_description="System spec v2")
        .add_package(id=pkg_id, name="Domain", provenance=prov)
        .add_element(id=sensor_id, kind=ElementKind.CLASS,
                     name="Sensor", package_id=pkg_id, provenance=prov)
        .add_element(id=collector_id, kind=ElementKind.CLASS,
                     name="DataCollector", package_id=pkg_id, provenance=prov)
        .add_relationship(kind=RelationshipKind.ASSOCIATION,
                          source_id=collector_id, target_id=sensor_id,
                          name="monitors", provenance=prov)
        .build()
    )
"""

from __future__ import annotations

import logging
from typing import Self

from ea_mbse_pipeline.canonical.diagram_models import (
    DiagramObject,
    ElementBounds,
    ModelDiagram,
)
from ea_mbse_pipeline.canonical.evidence_models import EvidenceLink
from ea_mbse_pipeline.canonical.ids import new_id
from ea_mbse_pipeline.canonical.models import (
    Attribute,
    CanonicalModel,
    ElementKind,
    ModelElement,
    ModelRelationship,
    Operation,
    Package,
    RelationshipKind,
    RequirementLink,
    RequirementLinkType,
    TaggedValue,
)
from ea_mbse_pipeline.canonical.uncertainty_models import (
    Uncertainty,
    UncertaintyLevel,
    UncertaintyType,
)
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.provenance import Provenance

logger = logging.getLogger(__name__)


class CanonicalModelBuilder:
    """Incrementally assembles a ``CanonicalModel``.

    All ``add_*`` methods return ``Self`` for chaining, except
    ``add_diagram`` which returns the new diagram's ``id``.
    Call ``build()`` to finalise and return the model.
    """

    def __init__(
        self,
        source_description: str = "",
        schema_version: str = "1.0",
    ) -> None:
        self._source_description = source_description
        self._schema_version = schema_version
        self._packages: list[Package] = []
        self._elements: list[ModelElement] = []
        self._relationships: list[ModelRelationship] = []
        self._diagrams: list[ModelDiagram] = []
        self._diagram_index: dict[str, ModelDiagram] = {}
        self._requirement_links: list[RequirementLink] = []
        self._evidence_links: list[EvidenceLink] = []
        self._uncertainties: list[Uncertainty] = []

    # ------------------------------------------------------------------
    # Package
    # ------------------------------------------------------------------

    def add_package(
        self,
        *,
        id: str | None = None,
        name: str,
        parent_id: str | None = None,
        path: str = "",
        stereotype: str | None = None,
        tagged_values: list[TaggedValue] | None = None,
        notes: str = "",
        provenance: Provenance,
    ) -> Self:
        pkg = Package(
            id=id or new_id(),
            name=name,
            parent_id=parent_id,
            path=path,
            stereotype=stereotype,
            tagged_values=tagged_values or [],
            notes=notes,
            provenance=provenance,
        )
        self._packages.append(pkg)
        logger.debug("Added package %r (%s)", pkg.name, pkg.id)
        return self

    # ------------------------------------------------------------------
    # Element
    # ------------------------------------------------------------------

    def add_element(
        self,
        *,
        id: str | None = None,
        kind: ElementKind,
        name: str,
        stereotype: str | None = None,
        package_id: str | None = None,
        ea_guid: str | None = None,
        attributes: list[Attribute] | None = None,
        operations: list[Operation] | None = None,
        tagged_values: list[TaggedValue] | None = None,
        notes: str = "",
        provenance: Provenance,
    ) -> Self:
        elem = ModelElement(
            id=id or new_id(),
            ea_guid=ea_guid,
            kind=kind,
            name=name,
            stereotype=stereotype,
            package_id=package_id,
            attributes=attributes or [],
            operations=operations or [],
            tagged_values=tagged_values or [],
            notes=notes,
            provenance=provenance,
        )
        self._elements.append(elem)
        logger.debug("Added element %r (%s)", elem.name, elem.id)
        return self

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------

    def add_relationship(
        self,
        *,
        id: str | None = None,
        kind: RelationshipKind,
        source_id: str,
        target_id: str,
        name: str = "",
        stereotype: str | None = None,
        tagged_values: list[TaggedValue] | None = None,
        provenance: Provenance,
    ) -> Self:
        rel = ModelRelationship(
            id=id or new_id(),
            kind=kind,
            source_id=source_id,
            target_id=target_id,
            name=name,
            stereotype=stereotype,
            tagged_values=tagged_values or [],
            provenance=provenance,
        )
        self._relationships.append(rel)
        logger.debug("Added relationship %s %s→%s", kind, source_id, target_id)
        return self

    # ------------------------------------------------------------------
    # Diagram
    # ------------------------------------------------------------------

    def add_diagram(
        self,
        *,
        id: str | None = None,
        name: str,
        diagram_type: str,
        package_id: str | None = None,
        provenance: Provenance,
    ) -> str:
        """Add a diagram and return its ``id`` for subsequent ``add_diagram_object`` calls."""
        diag_id = id or new_id()
        diag = ModelDiagram(
            id=diag_id,
            name=name,
            diagram_type=diagram_type,
            package_id=package_id,
            objects=[],
            provenance=provenance,
        )
        self._diagrams.append(diag)
        self._diagram_index[diag_id] = diag
        logger.debug("Added diagram %r (%s)", name, diag_id)
        return diag_id

    def add_diagram_object(
        self,
        *,
        diagram_id: str,
        element_id: str,
        id: str | None = None,
        bounds: ElementBounds | None = None,
    ) -> Self:
        """Add a ``DiagramObject`` to an existing diagram."""
        diag = self._diagram_index.get(diagram_id)
        if diag is None:
            raise PipelineError(
                ErrorCode.CANONICAL_DANGLING_REFERENCE,
                f"Diagram {diagram_id!r} not found when adding object "
                f"for element {element_id!r}",
                context={"diagram_id": diagram_id, "element_id": element_id},
            )
        obj = DiagramObject(id=id or new_id(), element_id=element_id, bounds=bounds)
        diag.objects.append(obj)
        return self

    # ------------------------------------------------------------------
    # Requirement link
    # ------------------------------------------------------------------

    def add_requirement_link(
        self,
        *,
        id: str | None = None,
        source_id: str,
        target_id: str,
        link_type: RequirementLinkType,
        notes: str = "",
        provenance: Provenance,
    ) -> Self:
        link = RequirementLink(
            id=id or new_id(),
            source_id=source_id,
            target_id=target_id,
            link_type=link_type,
            notes=notes,
            provenance=provenance,
        )
        self._requirement_links.append(link)
        logger.debug("Added requirement link %s %s→%s", link_type, source_id, target_id)
        return self

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------

    def add_evidence(
        self,
        *,
        id: str | None = None,
        element_id: str,
        provenance: Provenance,
        relevance_score: float | None = None,
        excerpt: str = "",
    ) -> Self:
        link = EvidenceLink(
            id=id or new_id(),
            element_id=element_id,
            provenance=provenance,
            relevance_score=relevance_score,
            excerpt=excerpt,
        )
        self._evidence_links.append(link)
        logger.debug("Added evidence for element %s", element_id)
        return self

    # ------------------------------------------------------------------
    # Uncertainty
    # ------------------------------------------------------------------

    def add_uncertainty(
        self,
        *,
        id: str | None = None,
        element_id: str,
        uncertainty_type: UncertaintyType,
        level: UncertaintyLevel,
        description: str,
        mitigation: str = "",
    ) -> Self:
        unc = Uncertainty(
            id=id or new_id(),
            element_id=element_id,
            uncertainty_type=uncertainty_type,
            level=level,
            description=description,
            mitigation=mitigation,
        )
        self._uncertainties.append(unc)
        logger.debug(
            "Added uncertainty (%s / %s) for element %s", uncertainty_type, level, element_id
        )
        return self

    # ------------------------------------------------------------------
    # Finalise
    # ------------------------------------------------------------------

    def build(self) -> CanonicalModel:
        """Return the assembled ``CanonicalModel``.  The builder remains usable after this call."""
        return CanonicalModel(
            schema_version=self._schema_version,
            source_description=self._source_description,
            packages=list(self._packages),
            elements=list(self._elements),
            relationships=list(self._relationships),
            diagrams=list(self._diagrams),
            requirement_links=list(self._requirement_links),
            evidence_links=list(self._evidence_links),
            uncertainties=list(self._uncertainties),
        )
