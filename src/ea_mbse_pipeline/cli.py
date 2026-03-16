"""CLI entry points.  All commands are placeholders until stages are implemented."""

from __future__ import annotations

import typer

from ea_mbse_pipeline.shared.logging import configure_logging

app      = typer.Typer(name="ea-mbse-pipeline", help="MBSE pipeline for Enterprise Architect 17.1.")
ingest   = typer.Typer(name="ea-ingest",   help="Run the ingestion stage only.")
validate = typer.Typer(name="ea-validate", help="Run the validation stage only.")
serialize= typer.Typer(name="ea-serialize",help="Run the serialization stage only.")


@app.callback()
def _main(log_level: str = typer.Option("INFO", help="Logging level.")) -> None:
    configure_logging(log_level)


@app.command("run")
def run_pipeline(
    input_path: str  = typer.Argument(..., help="Path to input file or directory."),
    metamodel: str   = typer.Option("data/raw/metamodel/ea17_base.xmi", help="XMI metamodel path."),
    output_dir: str  = typer.Option("outputs/", help="Output directory."),
) -> None:
    """Run the full MBSE pipeline on INPUT_PATH."""
    raise NotImplementedError("Full pipeline — milestone: Sprint 1")


@app.command("ingest")
def run_ingest(input_path: str = typer.Argument(...)) -> None:
    """Run only the ingestion stage."""
    raise NotImplementedError("Ingestion stage — milestone: Sprint 1")


@app.command("validate")
def run_validate(canonical_path: str = typer.Argument(...)) -> None:
    """Validate a canonical model JSON against the metamodel."""
    raise NotImplementedError("Validation stage — milestone: Sprint 1")


@app.command("serialize")
def run_serialize(canonical_path: str = typer.Argument(...)) -> None:
    """Serialize a canonical model JSON to EA XMI."""
    raise NotImplementedError("Serialization stage — milestone: Sprint 1")


if __name__ == "__main__":
    app()
