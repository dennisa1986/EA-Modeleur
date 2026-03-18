"""Canonical model ID generation and EA GUID conversion.

Pipeline-internal IDs
---------------------
Every canonical artefact (Package, ModelElement, ModelRelationship,
ModelDiagram, …) carries a *pipeline-internal ID* — a plain lowercase UUID4
string without any wrapping or casing convention:

    "3fa85f64-5717-4562-b3fc-2c963f66afa6"

These IDs are assigned at creation time and never re-derived from element
names or external sources, so they remain stable even when names change.

EA GUIDs
--------
When the serializer writes XMI for Enterprise Architect it converts
pipeline-internal IDs to EA-style GUIDs:

    "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"

The curly-brace wrapping and upper-casing are required by EA 17.1.
Only the serializer performs this conversion; the canonical layer stores
only the plain pipeline-internal ID.

Optional ``ea_guid`` field
--------------------------
``ModelElement`` carries an optional ``ea_guid`` field.  Populate it *only*
when ingesting a source that already contains EA GUIDs (e.g. a previously
exported XMI file).  For elements produced by the pipeline from scratch, leave
``ea_guid`` as ``None``; the serializer will derive it from ``id``.
"""

from __future__ import annotations

import uuid


def new_id() -> str:
    """Return a new pipeline-internal UUID4 string (lowercase, no braces)."""
    return str(uuid.uuid4())


def to_ea_guid(canonical_id: str) -> str:
    """Convert a pipeline-internal UUID to an EA-style GUID.

    >>> to_ea_guid("3fa85f64-5717-4562-b3fc-2c963f66afa6")
    '{3FA85F64-5717-4562-B3FC-2C963F66AFA6}'
    """
    return "{" + canonical_id.upper() + "}"


def from_ea_guid(ea_guid: str) -> str:
    """Strip curly braces from an EA GUID and lower-case it.

    >>> from_ea_guid("{3FA85F64-5717-4562-B3FC-2C963F66AFA6}")
    '3fa85f64-5717-4562-b3fc-2c963f66afa6'
    """
    return ea_guid.strip("{}").lower()


def is_valid_id(value: str) -> bool:
    """Return ``True`` iff *value* is a valid pipeline-internal UUID string.

    Pipeline-internal IDs must not have curly-brace wrapping (that format is
    reserved for EA GUIDs).  ``"{...}"`` strings are therefore rejected even
    though Python's ``uuid.UUID`` accepts them.
    """
    if value.startswith("{") or value.endswith("}"):
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
