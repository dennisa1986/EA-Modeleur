"""Metamodel compiler — Sprint 3 main entry point.

Orchestrates XMI parsing, optional description parsing, rule generation,
registry assembly, and export.  This is the concrete implementation of
``BaseMetamodelCompiler``.

Usage::

    from ea_mbse_pipeline.metamodel.compiler import MetamodelCompiler

    compiler = MetamodelCompiler()

    # Basic compile (XMI only)
    rule_set = compiler.compile(Path("data/raw/metamodel/model.xmi"))

    # With supplementary description
    rule_set = compiler.compile_full(
        Path("data/raw/metamodel/model.xmi"),
        description_path=Path("data/raw/metamodel/description.txt"),
    )

    # Compile and write JSON + Markdown output
    rule_set, json_path, md_path = compiler.compile_and_export(
        Path("data/raw/metamodel/model.xmi"),
        description_path=Path("data/raw/metamodel/description.txt"),
    )
"""

from __future__ import annotations

import logging
from pathlib import Path

from ea_mbse_pipeline.metamodel.description_parser import DescriptionParseResult, DescriptionParser
from ea_mbse_pipeline.metamodel.models import (
    ConnectorConstraint,
    ForbiddenPattern,
    MetamodelRule,
    RuleKind,
    RuleScope,
    RuleSet,
    TaggedValueConstraint,
)
from ea_mbse_pipeline.metamodel.protocols import BaseMetamodelCompiler
from ea_mbse_pipeline.metamodel.provenance import provenance_from_description, provenance_from_xmi
from ea_mbse_pipeline.metamodel.registry_export import RegistryExporter
from ea_mbse_pipeline.metamodel.rule_registry import RuleRegistry
from ea_mbse_pipeline.metamodel.xmi_parser import XMIParseResult, XMIParser
from ea_mbse_pipeline.settings import settings

logger = logging.getLogger(__name__)

# Rule-kind → rule-ID prefix
_KIND_PREFIX: dict[RuleKind, str] = {
    RuleKind.ELEMENT_TYPE: "R-ETYPE",
    RuleKind.STEREOTYPE: "R-STEREO",
    RuleKind.CONNECTOR: "R-CONN",
    RuleKind.TAGGED_VALUE: "R-TVAL",
    RuleKind.PACKAGE_PLACEMENT: "R-PKG",
    RuleKind.NAMING: "R-NAME",
    RuleKind.DIAGRAM: "R-DIAG",
    RuleKind.FORBIDDEN: "R-FORB",
    RuleKind.GENERAL: "R-GEN",
}

# Rule-kind → default scope
_KIND_SCOPE: dict[RuleKind, RuleScope] = {
    RuleKind.ELEMENT_TYPE: RuleScope.ELEMENT,
    RuleKind.STEREOTYPE: RuleScope.ELEMENT,
    RuleKind.CONNECTOR: RuleScope.RELATIONSHIP,
    RuleKind.TAGGED_VALUE: RuleScope.ELEMENT,
    RuleKind.PACKAGE_PLACEMENT: RuleScope.PACKAGE,
    RuleKind.NAMING: RuleScope.ELEMENT,
    RuleKind.DIAGRAM: RuleScope.DIAGRAM,
    RuleKind.FORBIDDEN: RuleScope.MODEL,
    RuleKind.GENERAL: RuleScope.MODEL,
}


class MetamodelCompiler(BaseMetamodelCompiler):
    """Compiles a metamodel XMI (+ optional description) into a ``RuleSet``.

    Each instance maintains its own rule-ID counters so that multiple
    compilations from the same instance produce unique, sequential IDs.
    """

    def __init__(self) -> None:
        self._xmi_parser = XMIParser()
        self._desc_parser = DescriptionParser()
        self._exporter = RegistryExporter()
        self._counters: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile(self, xmi_path: Path) -> RuleSet:
        """Satisfy ``BaseMetamodelCompiler`` contract (XMI only)."""
        return self.compile_full(xmi_path)

    def compile_full(
        self,
        xmi_path: Path,
        description_path: Path | None = None,
    ) -> RuleSet:
        """Compile XMI + optional description into a ``RuleSet``.

        Args:
            xmi_path:         Path to the XMI metamodel file.
            description_path: Optional path to a supplementary description file.
        """
        self._counters.clear()
        logger.info("Starting metamodel compilation: %s", xmi_path)

        xmi_result = self._xmi_parser.parse(xmi_path)

        desc_result: DescriptionParseResult | None = None
        if description_path is not None:
            desc_result = self._desc_parser.parse(description_path)

        registry = RuleRegistry()
        self._rules_from_xmi(xmi_result, str(xmi_path), registry)
        if desc_result is not None:
            self._rules_from_description(
                desc_result, str(description_path), str(xmi_path), registry
            )

        rule_set = registry.to_rule_set(
            source_xmi=str(xmi_path),
            ea_version=xmi_result.ea_version or settings.ea_version,
        )
        rule_set.element_types = [c.name for c in xmi_result.classes]
        rule_set.stereotypes = [s.name for s in xmi_result.stereotypes]
        if description_path is not None:
            rule_set.description_sources = [str(description_path)]

        logger.info(
            "Compilation complete: %d rules, %d element types, %d stereotypes",
            rule_set.rule_count,
            len(rule_set.element_types),
            len(rule_set.stereotypes),
        )
        return rule_set

    def compile_and_export(
        self,
        xmi_path: Path,
        description_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> tuple[RuleSet, Path, Path]:
        """Compile and write JSON + Markdown to *output_dir*.

        Output paths:
            ``<output_dir>/<xmi_stem>_registry.json``
            ``<output_dir>/<xmi_stem>_report.md``

        Returns:
            ``(rule_set, json_path, markdown_path)``
        """
        rule_set = self.compile_full(xmi_path, description_path)
        out_dir = output_dir or (settings.processed_dir / "metamodel")
        stem = xmi_path.stem
        json_path = self._exporter.export_json(rule_set, out_dir / f"{stem}_registry.json")
        md_path = self._exporter.export_markdown(rule_set, out_dir / f"{stem}_report.md")
        return rule_set, json_path, md_path

    # ------------------------------------------------------------------
    # Rule builders
    # ------------------------------------------------------------------

    def _next_id(self, kind: RuleKind) -> str:
        prefix = _KIND_PREFIX[kind]
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}-{self._counters[prefix]:03d}"

    def _rules_from_xmi(
        self,
        result: XMIParseResult,
        xmi_path: str,
        registry: RuleRegistry,
    ) -> None:
        # Element-type rules
        for cls in result.classes:
            prov = provenance_from_xmi(xmi_path, cls.xmi_ref)
            registry.add(
                MetamodelRule(
                    id=self._next_id(RuleKind.ELEMENT_TYPE),
                    kind=RuleKind.ELEMENT_TYPE,
                    scope=RuleScope.ELEMENT,
                    description=(
                        f"Element type '{cls.name}' ({cls.xmi_type}) is defined in the metamodel."
                    ),
                    constraint=f"element.type == '{cls.name}'",
                    severity="error",
                    source_xmi_ref=cls.xmi_ref,
                    provenance=prov,
                )
            )

            # Required tagged-value rules from ownedAttribute children
            for prop in cls.properties:
                registry.add(
                    MetamodelRule(
                        id=self._next_id(RuleKind.TAGGED_VALUE),
                        kind=RuleKind.TAGGED_VALUE,
                        scope=RuleScope.ELEMENT,
                        description=(
                            f"Element '{cls.name}' must carry tagged value '{prop.name}'."
                        ),
                        severity="error",
                        source_xmi_ref=cls.xmi_ref,
                        provenance=provenance_from_xmi(xmi_path, cls.xmi_ref),
                        tagged_value_constraint=TaggedValueConstraint(
                            tag_name=prop.name,
                            required=True,
                            applies_to_types=[cls.name],
                        ),
                    )
                )

        # Connector rules
        for conn in result.connectors:
            prov = provenance_from_xmi(xmi_path, conn.xmi_ref)
            registry.add(
                MetamodelRule(
                    id=self._next_id(RuleKind.CONNECTOR),
                    kind=RuleKind.CONNECTOR,
                    scope=RuleScope.RELATIONSHIP,
                    description=(
                        f"Connector '{conn.connector_type}' (name='{conn.name}') "
                        f"from '{conn.source_name or '?'}' to '{conn.target_name or '?'}' "
                        "is defined in the metamodel."
                    ),
                    severity="error",
                    source_xmi_ref=conn.xmi_ref,
                    provenance=prov,
                    connector_constraint=ConnectorConstraint(
                        connector_type=conn.connector_type,
                        source_types=[conn.source_name] if conn.source_name else [],
                        target_types=[conn.target_name] if conn.target_name else [],
                        allowed=True,
                    ),
                )
            )

        # Stereotype rules
        for stereo in result.stereotypes:
            xref = f"//Stereotype[@name='{stereo.name}']"
            registry.add(
                MetamodelRule(
                    id=self._next_id(RuleKind.STEREOTYPE),
                    kind=RuleKind.STEREOTYPE,
                    scope=RuleScope.ELEMENT,
                    description=f"Stereotype '{stereo.name}' is defined in the metamodel.",
                    constraint=f"element.stereotype == '{stereo.name}'",
                    severity="error",
                    source_xmi_ref=xref,
                    provenance=provenance_from_xmi(xmi_path, xref),
                )
            )

    def _rules_from_description(
        self,
        desc_result: DescriptionParseResult,
        desc_path: str,
        xmi_path: str,
        registry: RuleRegistry,
    ) -> None:
        kind_map: dict[str, RuleKind] = {
            "naming": RuleKind.NAMING,
            "tagged_value": RuleKind.TAGGED_VALUE,
            "package_placement": RuleKind.PACKAGE_PLACEMENT,
            "forbidden": RuleKind.FORBIDDEN,
            "connector": RuleKind.CONNECTOR,
            "general": RuleKind.GENERAL,
        }

        for constraint in desc_result.constraints:
            kind = kind_map.get(constraint.inferred_kind, RuleKind.GENERAL)
            scope = _KIND_SCOPE[kind]
            prov = provenance_from_description(
                desc_path,
                line=constraint.source_line,
                section=constraint.section,
                corroborating_xmi=xmi_path,
            )
            registry.add(
                MetamodelRule(
                    id=self._next_id(kind),
                    kind=kind,
                    scope=scope,
                    description=constraint.raw_text[:250],
                    severity=constraint.severity,
                    provenance=prov,
                    forbidden_pattern=(
                        ForbiddenPattern(description=constraint.raw_text)
                        if kind == RuleKind.FORBIDDEN
                        else None
                    ),
                )
            )
