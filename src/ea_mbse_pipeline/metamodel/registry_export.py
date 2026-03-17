"""Export a RuleSet to JSON and Markdown (Sprint 3).

JSON is the machine-readable form consumed by downstream validation.
Markdown is a human-readable report for review and documentation.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from ea_mbse_pipeline.metamodel.models import MetamodelRule, RuleSet
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

logger = logging.getLogger(__name__)


class RegistryExporter:
    """Exports a ``RuleSet`` to JSON and Markdown formats."""

    # ------------------------------------------------------------------
    # JSON export
    # ------------------------------------------------------------------

    def export_json(self, rule_set: RuleSet, output_path: Path) -> Path:
        """Write *rule_set* as pretty-printed JSON to *output_path*.

        Raises:
            PipelineError(META-004): if the file cannot be written.
        """
        logger.info("Exporting registry JSON to %s", output_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            payload = rule_set.model_dump(mode="json")
            output_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            raise PipelineError(
                ErrorCode.METAMODEL_REGISTRY_EXPORT_FAIL,
                f"Cannot write registry JSON to {output_path}: {exc}",
                context={"path": str(output_path), "error": str(exc)},
            ) from exc
        logger.info("Registry JSON written (%d rules)", rule_set.rule_count)
        return output_path

    # ------------------------------------------------------------------
    # Markdown report
    # ------------------------------------------------------------------

    def export_markdown(self, rule_set: RuleSet, output_path: Path) -> Path:
        """Write a human-readable Markdown validation report to *output_path*.

        Raises:
            PipelineError(META-004): if the file cannot be written.
        """
        logger.info("Exporting registry Markdown to %s", output_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            md = self.build_markdown(rule_set)
            output_path.write_text(md, encoding="utf-8")
        except Exception as exc:
            raise PipelineError(
                ErrorCode.METAMODEL_REGISTRY_EXPORT_FAIL,
                f"Cannot write Markdown report to {output_path}: {exc}",
                context={"path": str(output_path), "error": str(exc)},
            ) from exc
        logger.info("Markdown report written to %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Public content builder (also used by unit tests without I/O)
    # ------------------------------------------------------------------

    def build_markdown(self, rule_set: RuleSet) -> str:
        """Return the full Markdown report as a string (no file I/O)."""
        lines: list[str] = []
        lines += [
            "# Metamodel Constraint Registry",
            "",
            f"**Source XMI:** `{rule_set.source_xmi}`  ",
            f"**EA Version:** {rule_set.ea_version}  ",
            f"**Compiled at:** {rule_set.compiled_at.isoformat()}  ",
            f"**Total rules:** {rule_set.rule_count}  ",
            f"**Error rules:** {len(rule_set.error_rules)}  ",
            f"**Warning rules:** {len(rule_set.warning_rules)}  ",
            "",
        ]

        if rule_set.element_types:
            lines.append("## Element Types")
            for et in sorted(rule_set.element_types):
                lines.append(f"- `{et}`")
            lines.append("")

        if rule_set.stereotypes:
            lines.append("## Stereotypes")
            for st in sorted(rule_set.stereotypes):
                lines.append(f"- `{st}`")
            lines.append("")

        if rule_set.description_sources:
            lines.append("## Description Sources")
            for ds in rule_set.description_sources:
                lines.append(f"- `{ds}`")
            lines.append("")

        # Group rules by kind
        by_kind: dict[str, list[MetamodelRule]] = defaultdict(list)
        for rule in rule_set.rules:
            by_kind[rule.kind.value].append(rule)

        for kind in sorted(by_kind.keys()):
            heading = kind.replace("_", " ").title()
            lines.append(f"## Rules: {heading}")
            lines.append("")
            lines.append("| ID | Severity | Scope | Description |")
            lines.append("|---|---|---|---|")
            for rule in sorted(by_kind[kind], key=lambda r: r.id):
                desc = rule.description.replace("|", "\\|")
                lines.append(
                    f"| `{rule.id}` | {rule.severity} | {rule.scope.value} | {desc} |"
                )
            lines.append("")

            # Detail blocks for rules with typed constraints
            for rule in sorted(by_kind[kind], key=lambda r: r.id):
                detail = self._rule_detail(rule)
                if detail:
                    lines.append(f"### {rule.id}")
                    lines.append(detail)
                    lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _rule_detail(rule: MetamodelRule) -> str:
        """Return a Markdown detail block for a rule with typed constraints."""
        parts: list[str] = []

        if rule.constraint:
            parts.append(f"**Constraint:** `{rule.constraint}`")

        if rule.connector_constraint:
            cc = rule.connector_constraint
            parts.append(
                f"**Connector:** type=`{cc.connector_type}` "
                f"source={cc.source_types or '*'} "
                f"target={cc.target_types or '*'} "
                f"allowed={cc.allowed}"
            )

        if rule.tagged_value_constraint:
            tv = rule.tagged_value_constraint
            parts.append(
                f"**Tagged value:** `{tv.tag_name}` "
                f"required={tv.required} "
                f"pattern={tv.value_pattern or 'any'} "
                f"applies_to={tv.applies_to_types or 'all'}"
            )

        if rule.naming_constraint:
            nc = rule.naming_constraint
            parts.append(
                f"**Naming:** pattern=`{nc.pattern}` "
                f"applies_to={nc.applies_to_types or 'all'}"
            )

        if rule.package_placement:
            pp = rule.package_placement
            if pp.allowed_packages:
                parts.append(f"**Allowed packages:** {pp.allowed_packages}")
            if pp.forbidden_packages:
                parts.append(f"**Forbidden packages:** {pp.forbidden_packages}")

        if rule.diagram_constraint:
            dc = rule.diagram_constraint
            parts.append(f"**Diagram type:** `{dc.diagram_type}`")
            if dc.forbidden_element_types:
                parts.append(f"**Forbidden elements:** {dc.forbidden_element_types}")

        if rule.forbidden_pattern:
            fp = rule.forbidden_pattern
            parts.append(f"**Forbidden:** {fp.description}")

        if rule.provenance:
            prov = rule.provenance
            src_list = ", ".join(f"`{s.file_path}`" for s in prov.sources)
            parts.append(f"**Provenance:** {src_list} via `{prov.derivation_method}`")

        if rule.source_xmi_ref:
            parts.append(f"**XMI ref:** `{rule.source_xmi_ref}`")

        return "\n\n".join(parts) if parts else ""
