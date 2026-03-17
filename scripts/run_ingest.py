#!/usr/bin/env python3
"""Standalone ingest script — alternative to the ea-ingest CLI entry point.

Usage
-----
Run from the project root (after `uv sync --extra dev`):

    python scripts/run_ingest.py

With custom paths:

    python scripts/run_ingest.py \\
        --corpus-dir data/raw/corpus \\
        --metamodel-dir data/raw/metamodel \\
        --screenshots-dir data/raw/screenshots \\
        --output-dir data/processed/ingest \\
        --log-level INFO

Or via the installed CLI:

    ea-ingest \\
        --corpus-dir data/raw/corpus \\
        --metamodel-dir data/raw/metamodel

Output
------
Each run writes three files under OUTPUT_DIR/{run_id}/:
  manifest.json  — full IngestRunManifest (all fields, all chunks)
  chunks.json    — CorpusChunk list only (for retrieval stage)
  ingest.db      — SQLite database with four tables

Exit codes
----------
  0  success (zero errors)
  1  one or more files failed to ingest (partial success)
  2  storage failure (manifest could not be written)
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer

# Ensure the src/ layout is importable when run directly
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from ea_mbse_pipeline.ingest.pipeline import IngestPipeline  # noqa: E402
from ea_mbse_pipeline.shared.logging import configure_logging  # noqa: E402

app = typer.Typer(
    name="run_ingest",
    help="Run the ingest stage and write output to data/processed/ingest/.",
    add_completion=False,
)


@app.command()
def main(
    corpus_dir: str = typer.Option("data/raw/corpus", help="Corpus directory (PDF, txt, md)."),
    metamodel_dir: str = typer.Option("data/raw/metamodel", help="XMI metamodel directory."),
    screenshots_dir: str = typer.Option(
        "data/raw/screenshots", help="Screenshots directory (optional)."
    ),
    output_dir: str = typer.Option("data/processed/ingest", help="Output base directory."),
    log_level: str = typer.Option("INFO", help="Logging level (DEBUG/INFO/WARNING)."),
) -> None:
    """Run the MBSE ingest pipeline stage."""
    configure_logging(log_level)

    pipeline = IngestPipeline(
        corpus_dir=Path(corpus_dir),
        metamodel_dir=Path(metamodel_dir),
        screenshots_dir=Path(screenshots_dir),
        output_dir=Path(output_dir),
    )

    manifest = pipeline.run()

    finished = manifest.finished_at.isoformat() if manifest.finished_at else "N/A"
    typer.echo("=" * 60)
    typer.echo("Ingest run complete")
    typer.echo(f"  run_id     : {manifest.run_id}")
    typer.echo(f"  started    : {manifest.started_at.isoformat()}")
    typer.echo(f"  finished   : {finished}")
    typer.echo(f"  documents  : {manifest.document_count}")
    typer.echo(f"  chunks     : {manifest.chunk_count}")
    typer.echo(f"  images     : {len(manifest.image_assets)}")
    typer.echo(f"  xmi files  : {len(manifest.xmi_files)}")
    typer.echo(f"  errors     : {len(manifest.errors)}")
    typer.echo(f"  manifest   : {manifest.output_json_path}")
    typer.echo(f"  sqlite     : {manifest.output_sqlite_path}")
    typer.echo("=" * 60)

    if manifest.errors:
        typer.echo("\nErrors encountered:", err=True)
        for err in manifest.errors:
            typer.echo(f"  {err}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
