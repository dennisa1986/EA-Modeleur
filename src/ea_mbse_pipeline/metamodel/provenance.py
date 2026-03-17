"""Metamodel-specific provenance helpers (Sprint 3).

Thin helper layer that constructs ``shared.provenance`` objects from
metamodel parser outputs.  Does NOT redefine Provenance or SourceRef.
"""

from __future__ import annotations

from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef


def provenance_from_xmi(
    xmi_path: str,
    xmi_ref: str,
    *,
    extra_sources: list[SourceRef] | None = None,
) -> Provenance:
    """Build a Provenance for a rule derived directly from an XMI element.

    Args:
        xmi_path: Repo-relative or absolute path to the source XMI file.
        xmi_ref:  XPath-style locator string, e.g. ``//Class[@xmi:id='...']``.
        extra_sources: Additional SourceRef objects to include (optional).
    """
    sources: list[SourceRef] = [
        SourceRef(file_path=xmi_path, region=xmi_ref or None),
    ]
    if extra_sources:
        sources.extend(extra_sources)
    return Provenance(sources=sources, derivation_method="xmi-extraction")


def provenance_from_description(
    desc_path: str,
    line: int,
    section: str,
    *,
    corroborating_xmi: str | None = None,
    xmi_ref: str = "",
) -> Provenance:
    """Build a Provenance for a rule derived from a description document.

    Args:
        desc_path:         Path to the description file.
        line:              Source line number within the description file.
        section:           Section heading under which the constraint appeared.
        corroborating_xmi: Optional path to the XMI that corroborates this rule.
        xmi_ref:           XPath reference into the corroborating XMI (optional).
    """
    sources: list[SourceRef] = [
        SourceRef(file_path=desc_path, line=line, region=section or None),
    ]
    if corroborating_xmi:
        sources.append(
            SourceRef(file_path=corroborating_xmi, region=xmi_ref or None)
        )
    return Provenance(sources=sources, derivation_method="description-extraction")
