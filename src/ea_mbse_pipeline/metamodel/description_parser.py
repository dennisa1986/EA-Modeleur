"""Parser for supplementary textual description files (Sprint 3).

Reads plain-text or Markdown files that accompany XMI metamodels and
extracts additional constraints that cannot be encoded in XMI alone.
Extracted constraints are later merged into the rule registry by the
compiler.

Two extraction modes are supported:

1. **Heuristic mode** (Sprint 3) — lines containing MUST, SHALL, MUST NOT,
   SHALL NOT, FORBIDDEN, or PROHIBITED are treated as constraint statements.
   Kind and severity are inferred from keywords.  Classification is best-effort.

2. **Explicit mode** (Sprint 3.1) — lines matching the machine-friendly
   ``RULE[...]`` directive are parsed with exact metadata, bypassing
   heuristics entirely.  Format::

       RULE[kind=<kind>,severity=<severity>]: <constraint text>

   Both ``kind`` and ``severity`` are optional; omitted values default to
   ``general`` and ``error`` respectively.  Valid kind values: ``connector``,
   ``naming``, ``tagged_value``, ``package_placement``, ``forbidden``,
   ``general``.

   Explicit rules take priority: if a line starts with ``RULE[``, heuristic
   matching is skipped for that line.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

logger = logging.getLogger(__name__)

# Patterns that signal a normative constraint statement (heuristic mode)
_RE_MUST = re.compile(r"\bMUST\b", re.IGNORECASE)
_RE_SHALL = re.compile(r"\bSHALL\b", re.IGNORECASE)
_RE_FORBIDDEN = re.compile(
    r"\b(?:MUST NOT|SHALL NOT|FORBIDDEN|PROHIBITED|MAY NOT)\b", re.IGNORECASE
)

# Machine-friendly explicit rule directive (explicit mode)
# Matches: RULE[kind=foo,severity=bar]: <text>
# Both key=value pairs are optional; attrs group may be empty.
_RE_EXPLICIT_RULE = re.compile(
    r"^RULE\[(?P<attrs>[^\]]*)\]:\s*(?P<text>.+)",
    re.IGNORECASE,
)

# Accepted kind values for explicit rules
_VALID_EXPLICIT_KINDS = frozenset(
    {"connector", "naming", "tagged_value", "package_placement", "forbidden", "general"}
)
_VALID_EXPLICIT_SEVERITIES = frozenset({"error", "warning"})


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
    is_explicit: bool = False
    """True when extracted from a ``RULE[...]`` directive; False for heuristic."""


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

    Extraction order per non-blank, non-heading line:

    1. If the line matches ``RULE[...]:`` → explicit extraction (kind/severity
       read directly from the directive).
    2. Else if the line contains MUST / SHALL / FORBIDDEN → heuristic extraction
       (kind and severity inferred from keywords).
    3. Otherwise the line is silently skipped.
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
            "Description parse complete: %d constraints extracted (%d explicit, %d heuristic)",
            len(result.constraints),
            sum(1 for c in result.constraints if c.is_explicit),
            sum(1 for c in result.constraints if not c.is_explicit),
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

            # --- Explicit RULE[...] directive takes priority ---
            explicit = self._try_explicit_rule(cleaned, result)
            if explicit is not None:
                text_body, kind, severity = explicit
                result.constraints.append(
                    DescriptionConstraint(
                        raw_text=text_body,
                        inferred_kind=kind,
                        severity=severity,
                        source_line=lineno,
                        section=current_section,
                        is_explicit=True,
                    )
                )
                continue

            # --- Heuristic fallback: MUST / SHALL / FORBIDDEN ---
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
                    is_explicit=False,
                )
            )

    @staticmethod
    def _try_explicit_rule(
        line: str,
        result: DescriptionParseResult,
    ) -> tuple[str, str, str] | None:
        """Try to parse a ``RULE[attrs]: text`` directive.

        Returns ``(constraint_text, kind, severity)`` on success, ``None`` if
        the line does not match the directive format.

        Unrecognised kind or severity values are replaced with their defaults
        and a warning is recorded in *result*.
        """
        m = _RE_EXPLICIT_RULE.match(line)
        if not m:
            return None

        attrs_str = m.group("attrs")
        text_body = m.group("text").strip()
        kind = "general"
        severity = "error"

        for part in attrs_str.split(","):
            part = part.strip()
            if "=" not in part:
                continue
            key, _, val = part.partition("=")
            key = key.strip().lower()
            val = val.strip().lower()
            if key == "kind":
                if val in _VALID_EXPLICIT_KINDS:
                    kind = val
                else:
                    result.warnings.append(
                        f"Unknown kind '{val}' in RULE directive; defaulting to 'general'."
                    )
            elif key == "severity":
                if val in _VALID_EXPLICIT_SEVERITIES:
                    severity = val
                else:
                    result.warnings.append(
                        f"Unknown severity '{val}' in RULE directive; defaulting to 'error'."
                    )

        return text_body, kind, severity

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
