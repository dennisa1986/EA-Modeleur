"""JSON I/O for ``CanonicalModel`` with schema validation.

Provides fault-tolerant load and save helpers that validate against the
JSON Schema at ``schemas/canonical_model.schema.json``.

Error handling
--------------
All errors are raised as ``PipelineError`` with structured ``ErrorCode``s:

- ``CANONICAL_IO_READ_FAIL``      — file missing, permission error, or invalid JSON
- ``CANONICAL_SCHEMA_VIOLATION``  — JSON does not conform to the canonical schema
- ``CANONICAL_IO_WRITE_FAIL``     — cannot write to target path

Schema location
---------------
The schema is resolved relative to this source file at import time so the
helper works regardless of the current working directory.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import jsonschema.exceptions

from ea_mbse_pipeline.canonical.models import CanonicalModel
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError

logger = logging.getLogger(__name__)

# src/ea_mbse_pipeline/canonical/io.py → parents[3] == project root
_SCHEMA_PATH: Path = Path(__file__).parents[3] / "schemas" / "canonical_model.schema.json"


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    """Load and cache the canonical JSON Schema (loaded once per process)."""
    if not _SCHEMA_PATH.exists():
        raise PipelineError(
            ErrorCode.CANONICAL_SCHEMA_VIOLATION,
            f"Canonical schema file not found: {_SCHEMA_PATH}",
        )
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)  # type: ignore[no-any-return]


def validate_against_schema(data: dict[str, Any]) -> None:
    """Validate *data* against the canonical JSON Schema.

    Raises:
        PipelineError(CANONICAL_SCHEMA_VIOLATION) on any violation.
    """
    schema = _load_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as exc:
        raise PipelineError(
            ErrorCode.CANONICAL_SCHEMA_VIOLATION,
            f"Schema validation failed: {exc.message}",
            context={"path": list(exc.absolute_path)},
        ) from exc


def load_canonical_model(path: Path) -> CanonicalModel:
    """Load a ``CanonicalModel`` from *path* and validate against the schema.

    Raises:
        PipelineError(CANONICAL_IO_READ_FAIL)     — file missing, unreadable, or bad JSON
        PipelineError(CANONICAL_SCHEMA_VIOLATION) — schema validation fails
    """
    logger.info("Loading canonical model from %s", path)
    try:
        with path.open(encoding="utf-8") as fh:
            raw: dict[str, Any] = json.load(fh)
    except FileNotFoundError as exc:
        raise PipelineError(
            ErrorCode.CANONICAL_IO_READ_FAIL,
            f"Canonical model file not found: {path}",
            context={"path": str(path)},
        ) from exc
    except OSError as exc:
        raise PipelineError(
            ErrorCode.CANONICAL_IO_READ_FAIL,
            f"Cannot read canonical model: {exc}",
            context={"path": str(path)},
        ) from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(
            ErrorCode.CANONICAL_IO_READ_FAIL,
            f"Invalid JSON in canonical model file: {exc}",
            context={"path": str(path)},
        ) from exc

    validate_against_schema(raw)
    model = CanonicalModel.model_validate(raw)
    logger.info(
        "Loaded canonical model: %d packages, %d elements, %d relationships, %d diagrams",
        len(model.packages),
        len(model.elements),
        len(model.relationships),
        len(model.diagrams),
    )
    return model


def save_canonical_model(model: CanonicalModel, path: Path) -> None:
    """Serialise *model* to JSON at *path*, validating against schema first.

    Uses ``model_dump(mode='json', exclude_none=True)`` so the output is clean
    (no ``null`` values for optional fields).

    Raises:
        PipelineError(CANONICAL_SCHEMA_VIOLATION) — model violates the schema
        PipelineError(CANONICAL_IO_WRITE_FAIL)    — cannot write to *path*
    """
    logger.info("Saving canonical model to %s", path)
    data: dict[str, Any] = model.model_dump(mode="json", exclude_none=True)
    validate_against_schema(data)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise PipelineError(
            ErrorCode.CANONICAL_IO_WRITE_FAIL,
            f"Cannot write canonical model: {exc}",
            context={"path": str(path)},
        ) from exc
    logger.info("Saved canonical model to %s", path)
