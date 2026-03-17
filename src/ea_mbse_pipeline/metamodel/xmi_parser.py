"""XMI metamodel parser (Sprint 3).

Parses an EA XMI 2.1 metamodel file using lxml and returns a structured
``XMIParseResult`` containing element types, connectors, stereotypes, and
packages.  No rule-generation logic lives here — that belongs to
``compiler.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

logger = logging.getLogger(__name__)

# XMI/UML namespace constants
_NS_XMI = "http://www.omg.org/XMI"
_NS_UML = "http://www.eclipse.org/uml2/5.0.0/UML"

# xmi:type values that represent model element types (not connectors/packages)
_CLASS_LIKE_TYPES: frozenset[str] = frozenset(
    {
        "uml:Class",
        "uml:Interface",
        "uml:DataType",
        "uml:Enumeration",
        "uml:Signal",
        "uml:Component",
        "uml:Actor",
        "uml:UseCase",
        "uml:Node",
        "uml:Artifact",
    }
)

_CONNECTOR_TYPES: frozenset[str] = frozenset(
    {
        "uml:Association",
        "uml:Dependency",
        "uml:Realization",
        "uml:Usage",
        "uml:Abstraction",
        "uml:InformationFlow",
        "uml:AssociationClass",
        "uml:InterfaceRealization",
    }
)

_PACKAGE_TYPES: frozenset[str] = frozenset(
    {
        "uml:Package",
        "uml:Model",
    }
)


# ---------------------------------------------------------------------------
# Parse result data classes
# ---------------------------------------------------------------------------


@dataclass
class ParsedProperty:
    """An owned attribute / property on a class."""

    xmi_id: str
    name: str
    type_ref: str = ""


@dataclass
class ParsedClass:
    """An element type (Class, Interface, …) extracted from the XMI."""

    xmi_id: str
    name: str
    xmi_type: str
    """e.g. 'uml:Class', 'uml:Interface'"""
    stereotypes: list[str] = field(default_factory=list)
    properties: list[ParsedProperty] = field(default_factory=list)
    xmi_ref: str = ""
    """XPath-style locator for provenance."""


@dataclass
class ParsedConnector:
    """An association or dependency between elements."""

    xmi_id: str
    name: str
    connector_type: str
    source_id: str = ""
    target_id: str = ""
    source_name: str = ""
    target_name: str = ""
    xmi_ref: str = ""


@dataclass
class ParsedStereotype:
    """A stereotype definition found in the XMI."""

    name: str
    base_types: list[str] = field(default_factory=list)
    source: str = ""
    """'profile' | 'extension'"""


@dataclass
class ParsedPackage:
    """A package or model element."""

    xmi_id: str
    name: str
    parent_id: str = ""


@dataclass
class XMIParseResult:
    """Complete result of parsing a single XMI metamodel file."""

    source_path: str
    classes: list[ParsedClass] = field(default_factory=list)
    connectors: list[ParsedConnector] = field(default_factory=list)
    stereotypes: list[ParsedStereotype] = field(default_factory=list)
    packages: list[ParsedPackage] = field(default_factory=list)
    ea_version: str = ""
    raw_namespaces: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class XMIParser:
    """Parses an EA XMI 2.1 metamodel file.

    Raises:
        PipelineError(META-001): file not found or XML syntax error.
        PipelineError(META-002): XMI structure is not usable.
    """

    def parse(self, xmi_path: Path) -> XMIParseResult:
        if not xmi_path.exists():
            raise PipelineError(
                ErrorCode.METAMODEL_PARSE_ERROR,
                f"XMI file not found: {xmi_path}",
                context={"path": str(xmi_path)},
            )

        logger.info("Parsing XMI metamodel: %s", xmi_path)

        try:
            tree = etree.parse(str(xmi_path))  # noqa: S320
        except etree.XMLSyntaxError as exc:
            raise PipelineError(
                ErrorCode.METAMODEL_PARSE_ERROR,
                f"XML syntax error in {xmi_path}: {exc}",
                context={"path": str(xmi_path), "error": str(exc)},
            ) from exc

        root = tree.getroot()
        result = XMIParseResult(source_path=str(xmi_path))

        # Collect namespace map (skip None keys that lxml includes for default ns)
        result.raw_namespaces = {
            k: v for k, v in (root.nsmap or {}).items() if k is not None
        }
        result.ea_version = self._extract_ea_version(root)

        # Build an id → name index for resolving connector ends
        id_to_name = self._build_id_index(root)

        self._parse_packages(root, result)
        self._parse_classes(root, result)
        self._parse_connectors(root, result, id_to_name)
        self._parse_stereotypes(root, result)

        logger.info(
            "XMI parse complete: %d classes, %d connectors, %d stereotypes, %d packages",
            len(result.classes),
            len(result.connectors),
            len(result.stereotypes),
            len(result.packages),
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _xmi_attr(name: str) -> str:
        """Return a Clark-notation XMI attribute name, e.g. '{...XMI}type'."""
        return f"{{{_NS_XMI}}}{name}"

    def _extract_ea_version(self, root: etree._Element) -> str:
        for child in root:
            if not isinstance(child.tag, str):
                continue
            if "Documentation" in child.tag:
                version = child.get("exporterVersion", "")
                if version:
                    return version
                if "Enterprise Architect" in child.get("exporter", ""):
                    return "unknown-EA"
        return ""

    def _build_id_index(self, root: etree._Element) -> dict[str, str]:
        """Build id → name mapping for all named elements in the document."""
        xmi_id_attr = self._xmi_attr("id")
        index: dict[str, str] = {}
        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            xmi_id = elem.get(xmi_id_attr, "")
            name = elem.get("name", "")
            if xmi_id and name:
                index[xmi_id] = name
        return index

    def _parse_packages(self, root: etree._Element, result: XMIParseResult) -> None:
        xmi_id_attr = self._xmi_attr("id")
        xmi_type_attr = self._xmi_attr("type")
        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            xmi_type = elem.get(xmi_type_attr, "")
            tag_local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if xmi_type not in _PACKAGE_TYPES and tag_local not in ("Package", "Model"):
                continue
            xmi_id = elem.get(xmi_id_attr, "")
            name = elem.get("name", "")
            if not xmi_id:
                continue
            result.packages.append(ParsedPackage(xmi_id=xmi_id, name=name))

    def _parse_classes(self, root: etree._Element, result: XMIParseResult) -> None:
        xmi_id_attr = self._xmi_attr("id")
        xmi_type_attr = self._xmi_attr("type")
        seen_ids: set[str] = set()
        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            xmi_type = elem.get(xmi_type_attr, "")
            if xmi_type not in _CLASS_LIKE_TYPES:
                continue
            xmi_id = elem.get(xmi_id_attr, "")
            if xmi_id and xmi_id in seen_ids:
                continue  # Skip duplicate (e.g. element re-declared in xmi:Extension block)
            name = elem.get("name", "")
            if not name:
                result.warnings.append(
                    f"Skipping unnamed {xmi_type} element (xmi:id={xmi_id!r})"
                )
                continue

            parsed = ParsedClass(
                xmi_id=xmi_id,
                name=name,
                xmi_type=xmi_type,
                xmi_ref=self._xref(xmi_type, xmi_id),
            )

            # Collect ownedAttribute / ownedEnd children as properties
            for child in elem:
                if not isinstance(child.tag, str):
                    continue
                child_type = child.get(xmi_type_attr, "")
                if child_type == "uml:Property":
                    child_id = child.get(xmi_id_attr, "")
                    child_name = child.get("name", "")
                    if child_name:
                        parsed.properties.append(
                            ParsedProperty(
                                xmi_id=child_id,
                                name=child_name,
                                type_ref=child.get("type", ""),
                            )
                        )

            if xmi_id:
                seen_ids.add(xmi_id)
            result.classes.append(parsed)

    def _parse_connectors(
        self,
        root: etree._Element,
        result: XMIParseResult,
        id_to_name: dict[str, str],
    ) -> None:
        xmi_id_attr = self._xmi_attr("id")
        xmi_type_attr = self._xmi_attr("type")
        xmi_idref_attr = self._xmi_attr("idref")

        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            xmi_type = elem.get(xmi_type_attr, "")
            if xmi_type not in _CONNECTOR_TYPES:
                continue

            xmi_id = elem.get(xmi_id_attr, "")
            name = elem.get("name", "")

            # Resolve source/target from memberEnd children
            source_id = target_id = ""
            ends = elem.findall("memberEnd") or elem.findall("ownedEnd")
            if len(ends) >= 2:
                source_id = ends[0].get(xmi_idref_attr, "")
                target_id = ends[1].get(xmi_idref_attr, "")

            result.connectors.append(
                ParsedConnector(
                    xmi_id=xmi_id,
                    name=name,
                    connector_type=xmi_type,
                    source_id=source_id,
                    target_id=target_id,
                    source_name=id_to_name.get(source_id, ""),
                    target_name=id_to_name.get(target_id, ""),
                    xmi_ref=self._xref(xmi_type, xmi_id),
                )
            )

    def _parse_stereotypes(self, root: etree._Element, result: XMIParseResult) -> None:
        xmi_type_attr = self._xmi_attr("type")
        seen: set[str] = set()

        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            xmi_type = elem.get(xmi_type_attr, "")
            tag_local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            # UML profile-defined stereotypes
            if xmi_type == "uml:Stereotype" or tag_local == "Stereotype":
                name = elem.get("name", "")
                if name and name not in seen:
                    seen.add(name)
                    result.stereotypes.append(ParsedStereotype(name=name, source="profile"))

            # EA Extension-block stereotypes
            elif "Extension" in tag_local:
                for child in elem.iter():
                    if not isinstance(child.tag, str):
                        continue
                    child_local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if "stereotype" in child_local.lower():
                        st_name = child.get("name", "") or child.get("value", "")
                        if st_name and st_name not in seen:
                            seen.add(st_name)
                            result.stereotypes.append(
                                ParsedStereotype(name=st_name, source="extension")
                            )

    @staticmethod
    def _xref(xmi_type: str, xmi_id: str) -> str:
        """Build a compact XPath-style provenance reference."""
        # Use the local part of the type, e.g. 'Class' from 'uml:Class'
        local = xmi_type.split(":")[-1] if ":" in xmi_type else xmi_type
        return f"//{local}[@xmi:id='{xmi_id}']"
