# EA Modeleur — MBSE Pipeline

Production-grade MBSE pipeline that transforms raw input (text, images, PDFs, screenshots)
into validated, EA-importable model artefacts via a **mandatory canonical JSON intermediate model**.

Package: `ea_mbse_pipeline` · Python ≥ 3.11 · EA 17.1

---

## Pipeline

```
Raw Input (text / image / PDF / screenshot)     Metamodel (XMI)
               │                                      │
               ▼                                      ▼
       ┌──────────────┐                   ┌──────────────────────┐
       │    Ingest    │                   │  MetamodelCompiler   │
       └──────┬───────┘                   └──────────┬───────────┘
              │ RawContent                            │ RuleSet
              │                                       │
              └──────────────┬────────────────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │  Retrieval / Evidence │  corpus RAG, context enrichment
                 └───────────┬───────────┘
                             │ RetrievalResult
                             ▼
              ┌──────────────────────────────┐
              │      Canonical Model         │  ← MANDATORY intermediate layer
              │         (JSON)               │    schemas/canonical_model.schema.json
              └──────────────┬───────────────┘
                             │ CanonicalModel
                             ▼
                    ┌─────────────────┐
                    │   Validation    │◄── RuleSet
                    └────────┬────────┘
                             │ ValidationReport
                             ▼
                    ┌─────────────────┐
                    │  Serialization  │  pluggable — target format under validation
                    └────────┬────────┘
                             │ SerializedArtefact
                             ▼
                    ┌─────────────────┐
                    │   EA Checks     │  import validation + regression
                    └─────────────────┘
```

> **Serializer target format**: EA XMI 2.1 and CSV are the initial candidates.
> Whether a given format round-trips reliably through EA 17.1 for all element types
> is being validated before a production target is declared. The canonical model is
> the stable output contract; serializer plugins are interchangeable.

---

## Stage Overview

| Stage | Module | Input | Output |
|---|---|---|---|
| Ingest | `ea_mbse_pipeline.ingest` | file path | `RawContent` |
| MetamodelCompiler | `ea_mbse_pipeline.metamodel` | XMI path | `RuleSet` |
| Retrieval | `ea_mbse_pipeline.retrieval` | query + corpus | `RetrievalResult` |
| CanonicalBuilder | `ea_mbse_pipeline.canonical` | `RawContent` + evidence | `CanonicalModel` |
| Validator | `ea_mbse_pipeline.validation` | `CanonicalModel` + `RuleSet` | `ValidationReport` |
| Serializer | `ea_mbse_pipeline.serialization` | `CanonicalModel` | `SerializedArtefact` |
| EA Checks | `ea_mbse_pipeline.ea_test` | `SerializedArtefact` | `EATestReport` |

---

## Setup

```bash
pip install uv
uv sync --extra dev
```

## Commands

```bash
# Test
pytest                                           # full suite
pytest -m unit                                   # fast unit tests only
pytest --cov=ea_mbse_pipeline --cov-report=html  # with coverage

# Lint & type-check
ruff check src tests
mypy src

# CLI (stubs — stages not yet implemented)
ea-mbse-pipeline --help
ea-ingest --help
ea-validate --help
ea-serialize --help
```

---

## Project Layout

```
src/ea_mbse_pipeline/    Active pipeline package (Python ≥ 3.11)
  shared/                Cross-cutting: errors, logging, provenance, types
  ingest/                Stage: raw input → RawContent
  metamodel/             Stage: XMI → RuleSet
  retrieval/             Stage: corpus RAG → RetrievalResult
  canonical/             Stage: → CanonicalModel (mandatory intermediate)
  validation/            Stage: CanonicalModel + RuleSet → ValidationReport
  serialization/         Stage: CanonicalModel → SerializedArtefact (pluggable)
  ea_test/               Stage: post-serialization EA import checks
  orchestration/         PipelineOrchestrator (dependency injection)
  cli.py                 Typer CLI entry points
  settings.py            Pydantic-settings configuration

schemas/                 JSON Schema (canonical_model.schema.json is authoritative)

data/
  raw/metamodel/         XMI metamodel files — normative source of truth
  raw/corpus/            Text / PDF input documents
  fixtures/              Test input fixtures (committed)
  golden/                Reference outputs for regression (committed)

tests/
  unit/                  Isolated, no I/O (@pytest.mark.unit)
  integration/           Multi-stage wiring (@pytest.mark.integration)
  golden/                Byte-exact regression (@pytest.mark.golden)

.claude/
  agents/                Specialized Claude Code agents per pipeline role
  playbooks/             Step-by-step workflow guides
  rules/                 Coding and domain conventions
```

---

## Non-Negotiable Rules

- **Canonical model is mandatory** — every pipeline run passes through `CanonicalModel`.
- **Metamodel XMI is normative** — metamodel rules override all other heuristics.
- **No silent degradation** — serializers raise typed `PipelineError` on unmappable elements.
- **Provenance on every element** — every `ModelElement`, `ModelRelationship`, `ModelDiagram`
  carries a `Provenance` with at least one `SourceRef`.
- **Screenshots are supporting only** — image-derived elements need a corroborating
  text or metamodel `SourceRef`.
