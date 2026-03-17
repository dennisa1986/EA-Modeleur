"""CLI entry points for the MBSE pipeline."""

from __future__ import annotations

from pathlib import Path

import typer

from ea_mbse_pipeline.shared.logging import configure_logging

app      = typer.Typer(name="ea-mbse-pipeline", help="MBSE pipeline for Enterprise Architect 17.1.")
ingest   = typer.Typer(name="ea-ingest",   help="Run the ingestion stage over corpus, metamodel, and screenshot directories.")
validate = typer.Typer(name="ea-validate", help="Run the validation stage only.")
serialize = typer.Typer(name="ea-serialize", help="Run the serialization stage only.")


@app.callback()
def _main(log_level: str = typer.Option("INFO", help="Logging level.")) -> None:
    configure_logging(log_level)


@app.command("run")
def run_pipeline(
    input_path: str = typer.Argument(..., help="Path to input file or directory."),
    metamodel: str  = typer.Option("data/raw/metamodel/ea17_base.xmi", help="XMI metamodel path."),
    output_dir: str = typer.Option("outputs/", help="Output directory."),
) -> None:
    """Run the full MBSE pipeline on INPUT_PATH."""
    raise NotImplementedError("Full pipeline — milestone: Sprint 2")


@app.command("ingest")
def run_ingest_app(
    corpus_dir: str     = typer.Option("data/raw/corpus",      help="Corpus directory."),
    metamodel_dir: str  = typer.Option("data/raw/metamodel",   help="XMI metamodel directory."),
    screenshots_dir: str = typer.Option("data/raw/screenshots", help="Screenshots directory."),
    output_dir: str     = typer.Option("data/processed/ingest", help="Output base directory."),
    log_level: str      = typer.Option("INFO",                  help="Logging level."),
) -> None:
    """Run the ingestion stage (also available as the ea-ingest command)."""
    _do_ingest(corpus_dir, metamodel_dir, screenshots_dir, output_dir, log_level)


@app.command("validate")
def run_validate(canonical_path: str = typer.Argument(...)) -> None:
    """Validate a canonical model JSON against the metamodel."""
    raise NotImplementedError("Validation stage — milestone: Sprint 2")


@app.command("serialize")
def run_serialize(canonical_path: str = typer.Argument(...)) -> None:
    """Serialize a canonical model JSON to EA XMI."""
    raise NotImplementedError("Serialization stage — milestone: Sprint 2")


# ---------------------------------------------------------------------------
# ea-ingest standalone entry point
# ---------------------------------------------------------------------------

@ingest.callback(invoke_without_command=True)
def run_ingest_cmd(
    ctx: typer.Context,
    corpus_dir: str      = typer.Option("data/raw/corpus",       help="Corpus directory."),
    metamodel_dir: str   = typer.Option("data/raw/metamodel",    help="XMI metamodel directory."),
    screenshots_dir: str = typer.Option("data/raw/screenshots",  help="Screenshots directory."),
    output_dir: str      = typer.Option("data/processed/ingest", help="Output base directory."),
    log_level: str       = typer.Option("INFO",                  help="Logging level."),
) -> None:
    """Run the ingestion stage over corpus, metamodel, and screenshot directories.

    Writes output to OUTPUT_DIR/{run_id}/manifest.json, chunks.json, ingest.db.
    """
    if ctx.invoked_subcommand is not None:
        return
    _do_ingest(corpus_dir, metamodel_dir, screenshots_dir, output_dir, log_level)


def _do_ingest(
    corpus_dir: str,
    metamodel_dir: str,
    screenshots_dir: str,
    output_dir: str,
    log_level: str,
) -> None:
    """Shared implementation for both `ea-mbse-pipeline ingest` and `ea-ingest`."""
    configure_logging(log_level)
    from ea_mbse_pipeline.ingest.pipeline import IngestPipeline  # lazy import

    pipeline = IngestPipeline(
        corpus_dir=Path(corpus_dir),
        metamodel_dir=Path(metamodel_dir),
        screenshots_dir=Path(screenshots_dir),
        output_dir=Path(output_dir),
    )
    manifest = pipeline.run()

    typer.echo(f"Ingest complete  run_id={manifest.run_id}")
    typer.echo(f"  Documents : {manifest.document_count}")
    typer.echo(f"  Chunks    : {manifest.chunk_count}")
    typer.echo(f"  Images    : {len(manifest.image_assets)}")
    typer.echo(f"  XMI files : {len(manifest.xmi_files)}")
    typer.echo(f"  Errors    : {len(manifest.errors)}")
    if manifest.errors:
        for err in manifest.errors:
            typer.echo(f"    [ERROR] {err}", err=True)
    typer.echo(f"  Output    : {manifest.output_json_path}")

    if manifest.errors:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
