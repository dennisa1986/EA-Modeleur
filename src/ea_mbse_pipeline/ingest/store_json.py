"""Persist ingest artefacts to JSON files.

Writes two files per run:
  manifest.json  — full IngestRunManifest (all fields)
  chunks.json    — CorpusChunk list only (optimised for retrieval stage)

Both files are UTF-8 encoded and pretty-printed with 2-space indentation.
"""

from __future__ import annotations

import json
from pathlib import Path

from ea_mbse_pipeline.ingest.models import IngestRunManifest
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)


def save_manifest_json(manifest: IngestRunManifest, output_path: Path) -> Path:
    """Write *manifest* as a pretty-printed JSON file at *output_path*.

    Creates parent directories if they do not exist.

    Args:
        manifest:    The IngestRunManifest to serialise.
        output_path: Destination file path (e.g. ``output_dir/run_id/manifest.json``).

    Returns:
        The resolved output path.

    Raises:
        PipelineError(INGEST_READ_FAILURE): If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise PipelineError(
            ErrorCode.INGEST_READ_FAILURE,
            f"Cannot write manifest JSON to '{output_path}': {exc}",
            context={"path": str(output_path)},
        ) from exc

    logger.info(
        "Manifest saved → %s (%d bytes)",
        output_path,
        output_path.stat().st_size,
    )
    return output_path


def save_chunks_json(manifest: IngestRunManifest, output_path: Path) -> Path:
    """Write only the CorpusChunk list as JSON at *output_path*.

    Produces a slimmer file that the retrieval stage can load without
    deserialising the full manifest.  Format::

        {
          "run_id": "...",
          "chunk_count": N,
          "chunks": [...]
        }

    Args:
        manifest:    Source manifest.
        output_path: Destination file path (e.g. ``output_dir/run_id/chunks.json``).

    Returns:
        The resolved output path.

    Raises:
        PipelineError(INGEST_READ_FAILURE): If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": manifest.run_id,
        "chunk_count": manifest.chunk_count,
        "chunks": [chunk.model_dump(mode="json") for chunk in manifest.chunks],
    }
    try:
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise PipelineError(
            ErrorCode.INGEST_READ_FAILURE,
            f"Cannot write chunks JSON to '{output_path}': {exc}",
            context={"path": str(output_path)},
        ) from exc

    logger.info(
        "Chunks saved → %s (%d chunk(s))",
        output_path,
        manifest.chunk_count,
    )
    return output_path
