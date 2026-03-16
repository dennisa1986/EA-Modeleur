# EA Modeleur — MBSE Pipeline for Enterprise Architect 17.1

A production-grade pipeline that transforms raw input (text, images, PDFs) into
validated, EA-importable model artefacts via a canonical JSON intermediate model.

## Pipeline Overview

```
Raw Input                Metamodel (XMI)
    │                         │
    ▼                         ▼
┌─────────┐         ┌──────────────────┐
│Ingestor │         │MetamodelCompiler │
└────┬────┘         └────────┬─────────┘
     │                       │ rules
     ▼                       ▼
┌─────────────────────────────────────┐
│          CanonicalModel (JSON)      │
└─────────────────┬───────────────────┘
                  │
                  ▼
         ┌─────────────┐
         │  Validator  │◄── metamodel rules
         └──────┬──────┘
                │
                ▼
        ┌─────────────┐
        │ Serializer  │
        └──────┬──────┘
               │
               ▼
      ┌─────────────────┐
      │ EA XMI / CSV    │
      └────────┬────────┘
               │
               ▼
      ┌─────────────────┐
      │ImportValidator  │
      │ + Regression    │
      └─────────────────┘
```

## Pipeline Stages

| Stage | Module | Input | Output |
|---|---|---|---|
| Ingestor | `ea_pipeline.ingestion` | text / image / PDF | raw structured dict |
| MetamodelCompiler | `ea_pipeline.metamodel` | XMI file | `RuleSet` |
| CanonicalModel | `ea_pipeline.canonical` | structured dict | `CanonicalModel` JSON |
| Validator | `ea_pipeline.validation` | `CanonicalModel` + `RuleSet` | `ValidationReport` |
| Serializer | `ea_pipeline.serialization` | validated `CanonicalModel` | EA XMI / CSV |
| ImportValidator | `ea_pipeline.import_validation` | serialized artefact | `ImportReport` |

## Setup

```bash
# Install uv (if not already installed)
pip install uv

# Create venv and install all dependencies
uv sync --extra dev
```

## Commands

```bash
# Run the full test suite
pytest

# Run only unit tests (fast)
pytest -m unit

# Run with coverage
pytest --cov=ea_pipeline --cov-report=html

# Lint
ruff check src tests

# Type-check
mypy src

# Run the CLI
ea-pipeline --help
```

## Project Layout

```
src/ea_pipeline/       Core pipeline package
  ingestion/           Stage 1 — raw input processing
  metamodel/           Stage 2 — XMI metamodel → rules
  canonical/           Stage 3 — canonical JSON model
  validation/          Stage 4 — rule-based validation
  serialization/       Stage 5 — EA XMI/CSV output
  import_validation/   Stage 6 — post-import checks
  pipeline.py          Orchestrator that wires all stages
  settings.py          Pydantic-settings configuration
  cli.py               Typer CLI entry point
schemas/               JSON Schema files (data contracts between stages)
metamodels/            XMI metamodel input files
tests/
  unit/                Isolated per-stage tests
  integration/         Multi-stage wiring tests
  regression/          Golden-file tests against known EA outputs
    fixtures/          Reference XMI / canonical JSON golden files
.claude/
  agents/              Specialised Claude Code agents
  skills/              Reusable Claude Code skills
  rules/               Coding and domain conventions
```
