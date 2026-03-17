"""Parser for supplementary textual description files (Sprint 3).

Reads plain-text or Markdown files that accompany XMI metamodels and
extracts additional constraints that cannot be encoded in XMI alone.
Extracted constraints are later merged into the rule registry by the
compiler.

Classification is best-effort: a human reviewer should check inferred
rule kinds after compilation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

logger = logging.getLogger(__name__)

# Patterns that signal a normative constraint statement
_RE_MUST = re.compile(r"\bMUST\b", re.IGNORECASE)
_RE_SHALL = re.compile(r"\bSHALL\b", re.IGNORECASE)
_RE_FORBIDDEN = re.compile(
    r"\b(?:MUST NOT|SHALL NOT|FORBIDDEN|PROHIBITED|MAY NOT)\b", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------


@dataclass
class DescriptionConstraint:
    """A constraint sentence extracted from a description document."""

    raw_text: str
    """Original sentence or bullet point."""
    inferred_kind: str
    """Best-effort kind: 'connector' | 'naming' | 'tagged_value' |
    'package_placement' | 'forbidden' | 'general'."""
    severity: str = "error"
    source_line: int = 0
    section: str = ""


@dataclass
class DescriptionParseResult:
    """Result of parsing a supplementary description file."""

    source_path: str
    constraints: list[DescriptionConstraint] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class DescriptionParser:
    """Parses plain-text / Markdown description files for metamodel constraints.

    Only lines that contain MUST, SHALL, MUST NOT, SHALL NOT, FORBIDDEN, or
    PROHIBITED are treated as constraint statements.  All other lines are
    silently skipped.
    """

    def parse(self, description_path: Path) -> DescriptionParseResult:
        """Parse *description_path* and return extracted constraints.

        Raises:
            PipelineError(META-005): file not found or unreadable.
        """
        if not description_path.exists():
            raise PipelineError(
                ErrorCode.METAMODEL_DESCRIPTION_PARSE_ERROR,
                f"Description file not found: {description_path}",
                context={"path": str(description_path)},
            )

        logger.info("Parsing description file: %s", description_path)
        try:
            text = description_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PipelineError(
                ErrorCode.METAMODEL_DESCRIPTION_PARSE_ERROR,
                f"Cannot read description file {description_path}: {exc}",
                context={"path": str(description_path), "error": str(exc)},
            ) from exc

        result = DescriptionParseResult(source_path=str(description_path))
        self._parse_text(text, result)
        logger.info(
            "Description parse complete: %d constraints extracted",
            len(result.constraints),
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_text(self, text: str, result: DescriptionParseResult) -> None:
        current_section = ""
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # Markdown heading → new section
            if stripped.startswith("#"):
                current_section = stripped.lstrip("#").strip()
                if current_section not in result.sections:
                    result.sections.append(current_section)
                continue

            # Strip leading bullet/list markers
            cleaned = re.sub(r"^[-*+]\s+", "", stripped)

            if not self._is_constraint_line(cleaned):
                continue

            kind = self._infer_kind(cleaned)
            severity = self._infer_severity(cleaned)
            result.constraints.append(
                DescriptionConstraint(
                    raw_text=cleaned,
                    inferred_kind=kind,
                    severity=severity,
                    source_line=lineno,
                    section=current_section,
                )
            )

    @staticmethod
    def _is_constraint_line(line: str) -> bool:
        return bool(
            _RE_MUST.search(line) or _RE_SHALL.search(line) or _RE_FORBIDDEN.search(line)
        )

    @staticmethod
    def _infer_severity(line: str) -> str:
        """'error' for MUST/SHALL/FORBIDDEN; 'warning' for softer phrasing."""
        if _RE_FORBIDDEN.search(line) or _RE_MUST.search(line) or _RE_SHALL.search(line):
            return "error"
        return "warning"

    @staticmethod
    def _infer_kind(line: str) -> str:
        """Best-effort classification of constraint kind from line content."""
        lower = line.lower()
        # Tagged value: mentions tag or tagged value
        if any(kw in lower for kw in ("tagged value", "tagged-value", "tag name", " tag ")):
            return "tagged_value"
        # Naming: mentions name pattern / format / convention
        if any(kw in lower for kw in ("name pattern", "name format", "naming", "name convention")):
            return "naming"
        # Name start / case rule (e.g. "names MUST start with uppercase")
        if "name" in lower and any(kw in lower for kw in ("start with", "begin with", "lowercase", "uppercase", "capital")):
            return "naming"
        # Package placement
        if "package" in lower or "placed in" in lower or "reside in" in lower:
            return "package_placement"
        # Forbidden combination
        if _RE_FORBIDDEN.search(line):
            return "forbidden"
        # Connector / relationship
        if any(kw in lower for kw in ("connector", "association", "dependency", "relation")):
            return "connector"
        return "general"
