"""Persist ingest artefacts to a SQLite database.

Schema:
  ingest_runs       — one row per IngestPipeline.run() call
  source_documents  — one row per ingested source file
  corpus_chunks     — one row per CorpusChunk (indexed for retrieval)
  image_assets      — one row per discovered image

All JSON-typed columns (arrays, objects) are stored as TEXT.
All inserts use INSERT OR REPLACE for idempotency within a run.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ea_mbse_pipeline.ingest.models import IngestRunManifest
from ea_mbse_pipeline.shared.errors import ErrorCode, PipelineError
from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id           TEXT PRIMARY KEY,
    started_at       TEXT NOT NULL,
    finished_at      TEXT,
    corpus_dir       TEXT NOT NULL,
    metamodel_dir    TEXT NOT NULL,
    screenshots_dir  TEXT NOT NULL,
    errors           TEXT,
    warnings         TEXT
);

CREATE TABLE IF NOT EXISTS source_documents (
    doc_id           TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    file_path        TEXT NOT NULL,
    file_name        TEXT NOT NULL,
    source_type      TEXT NOT NULL,
    file_size_bytes  INTEGER,
    page_count       INTEGER,
    char_count       INTEGER,
    created_at       TEXT NOT NULL,
    metadata         TEXT,
    FOREIGN KEY (run_id) REFERENCES ingest_runs(run_id)
);

CREATE TABLE IF NOT EXISTS corpus_chunks (
    chunk_id             TEXT PRIMARY KEY,
    run_id               TEXT NOT NULL,
    doc_id               TEXT NOT NULL,
    source_file          TEXT NOT NULL,
    source_type          TEXT NOT NULL,
    page_start           INTEGER,
    page_end             INTEGER,
    section_title        TEXT,
    text                 TEXT NOT NULL,
    char_count           INTEGER,
    detected_keywords    TEXT,
    created_at           TEXT NOT NULL,
    object_type          TEXT,
    discipline           TEXT,
    provenance_sources   TEXT,
    FOREIGN KEY (doc_id) REFERENCES source_documents(doc_id)
);

CREATE TABLE IF NOT EXISTS image_assets (
    asset_id         TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    file_path        TEXT NOT NULL,
    source_doc_id    TEXT,
    page             INTEGER,
    width_px         INTEGER,
    height_px        INTEGER,
    format           TEXT,
    description      TEXT,
    created_at       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc_id     ON corpus_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source     ON corpus_chunks(source_file);
CREATE INDEX IF NOT EXISTS idx_docs_run_id       ON source_documents(run_id);
CREATE INDEX IF NOT EXISTS idx_images_run_id     ON image_assets(run_id);
"""


def save_to_sqlite(manifest: IngestRunManifest, db_path: Path) -> Path:
    """Write the full ingest manifest into a SQLite database at *db_path*.

    Creates parent directories if they do not exist.  Uses INSERT OR REPLACE
    so re-running the same run_id is idempotent.

    Args:
        manifest: The IngestRunManifest to persist.
        db_path:  Destination SQLite file (e.g. ``output_dir/run_id/ingest.db``).

    Returns:
        The resolved db_path.

    Raises:
        PipelineError(INGEST_READ_FAILURE): If the database cannot be written.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.executescript(_DDL)
            _insert_run(conn, manifest)
            _insert_documents(conn, manifest)
            _insert_chunks(conn, manifest)
            _insert_images(conn, manifest)
            conn.commit()
    except sqlite3.Error as exc:
        raise PipelineError(
            ErrorCode.INGEST_READ_FAILURE,
            f"Cannot write SQLite database '{db_path}': {exc}",
            context={"path": str(db_path)},
        ) from exc

    logger.info("SQLite DB saved → %s", db_path)
    return db_path


# ---------------------------------------------------------------------------
# Internal insert helpers
# ---------------------------------------------------------------------------


def _insert_run(conn: sqlite3.Connection, m: IngestRunManifest) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO ingest_runs
           (run_id, started_at, finished_at, corpus_dir, metamodel_dir,
            screenshots_dir, errors, warnings)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            m.run_id,
            m.started_at.isoformat(),
            m.finished_at.isoformat() if m.finished_at else None,
            m.corpus_dir,
            m.metamodel_dir,
            m.screenshots_dir,
            json.dumps(m.errors),
            json.dumps(m.warnings),
        ),
    )


def _insert_documents(conn: sqlite3.Connection, m: IngestRunManifest) -> None:
    for doc in m.source_documents:
        conn.execute(
            """INSERT OR REPLACE INTO source_documents
               (doc_id, run_id, file_path, file_name, source_type,
                file_size_bytes, page_count, char_count, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc.doc_id,
                m.run_id,
                doc.file_path,
                doc.file_name,
                doc.source_type,
                doc.file_size_bytes,
                doc.page_count,
                doc.char_count,
                doc.created_at.isoformat(),
                json.dumps(doc.metadata),
            ),
        )


def _insert_chunks(conn: sqlite3.Connection, m: IngestRunManifest) -> None:
    for chunk in m.chunks:
        prov = [s.model_dump() for s in chunk.provenance_sources]
        conn.execute(
            """INSERT OR REPLACE INTO corpus_chunks
               (chunk_id, run_id, doc_id, source_file, source_type,
                page_start, page_end, section_title, text, char_count,
                detected_keywords, created_at, object_type, discipline,
                provenance_sources)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk.chunk_id,
                m.run_id,
                chunk.doc_id,
                chunk.source_file,
                chunk.source_type,
                chunk.page_start,
                chunk.page_end,
                chunk.section_title,
                chunk.text,
                chunk.char_count,
                json.dumps(chunk.detected_keywords),
                chunk.created_at.isoformat(),
                chunk.object_type,
                chunk.discipline,
                json.dumps(prov),
            ),
        )


def _insert_images(conn: sqlite3.Connection, m: IngestRunManifest) -> None:
    for asset in m.image_assets:
        conn.execute(
            """INSERT OR REPLACE INTO image_assets
               (asset_id, run_id, file_path, source_doc_id, page,
                width_px, height_px, format, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                asset.asset_id,
                m.run_id,
                asset.file_path,
                asset.source_doc_id,
                asset.page,
                asset.width_px,
                asset.height_px,
                asset.format,
                asset.description,
                asset.created_at.isoformat(),
            ),
        )
