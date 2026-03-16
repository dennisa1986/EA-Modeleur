"""Typer CLI entry point.  Run: ea-pipeline --help"""

import typer

app = typer.Typer(name="ea-pipeline", help="MBSE pipeline for Enterprise Architect 17.1.")


@app.command()
def run(
    input_path: str = typer.Argument(..., help="Path to the raw input file or directory."),
    metamodel: str = typer.Option("metamodels/ea17_base.xmi", help="Path to XMI metamodel."),
    output: str = typer.Option("output/", help="Output directory for EA artefacts."),
) -> None:
    """Run the full MBSE pipeline on INPUT_PATH."""
    raise NotImplementedError("Pipeline execution not yet implemented.")


if __name__ == "__main__":
    app()
