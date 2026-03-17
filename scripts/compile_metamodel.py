#!/usr/bin/env python3
"""Compile a metamodel XMI into a constraint registry (Sprint 3).

Usage examples::

    # XMI only — output goes to data/processed/metamodel/
    python scripts/compile_metamodel.py data/raw/metamodel/model.xmi

    # XMI + supplementary description
    python scripts/compile_metamodel.py data/raw/metamodel/model.xmi \\
        --description data/raw/metamodel/description.txt

    # Custom output directory
    python scripts/compile_metamodel.py data/raw/metamodel/model.xmi \\
        --output-dir outputs/metamodel

Output files
------------
    <output_dir>/<xmi_stem>_registry.json   Machine-readable rule registry
    <output_dir>/<xmi_stem>_report.md       Human-readable Markdown report
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ea_mbse_pipeline.metamodel.compiler import MetamodelCompiler
from ea_mbse_pipeline.shared.errors import PipelineError
from ea_mbse_pipeline.shared.logging import configure_logging

app = typer.Typer(name="compile-metamodel", add_completion=False)
console = Console()


@app.command()
def main(
    xmi_path: Path = typer.Argument(
        ...,
        help="Path to the XMI metamodel file.",
        exists=True,
        readable=True,
    ),
    description: Path | None = typer.Option(
        None,
        "--description",
        "-d",
        help="Path to a supplementary description file (plain text or Markdown).",
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory. Defaults to data/processed/metamodel/.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable DEBUG logging."),
) -> None:
    """Compile a metamodel XMI into a JSON constraint registry and Markdown report."""
    configure_logging(level="DEBUG" if verbose else "INFO")
    logger = logging.getLogger(__name__)

    console.print(f"\n[bold]Metamodel Compiler[/bold] — [cyan]{xmi_path}[/cyan]")
    if description:
        console.print(f"  Description : [cyan]{description}[/cyan]")

    try:
        compiler = MetamodelCompiler()
        rule_set, json_path, md_path = compiler.compile_and_export(
            xmi_path,
            description_path=description,
            output_dir=output_dir,
        )
    except PipelineError as exc:
        console.print(f"\n[bold red]ERROR [{exc.code}][/bold red] {exc.message}")
        if exc.context:
            for k, v in exc.context.items():
                console.print(f"  {k}: {v}")
        logger.debug("PipelineError context: %s", exc.context)
        raise typer.Exit(code=1) from exc

    # Summary table
    table = Table(title="Compilation Summary", show_header=True)
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("EA Version", rule_set.ea_version)
    table.add_row("Element types", str(len(rule_set.element_types)))
    table.add_row("Stereotypes", str(len(rule_set.stereotypes)))
    table.add_row("Total rules", str(rule_set.rule_count))
    table.add_row("  Error rules", str(len(rule_set.error_rules)))
    table.add_row("  Warning rules", str(len(rule_set.warning_rules)))
    table.add_row("JSON registry", str(json_path))
    table.add_row("Markdown report", str(md_path))
    console.print(table)

    console.print("\n[green]Compilation complete.[/green]")


if __name__ == "__main__":
    app()
