# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Production-grade MBSE pipeline that transforms raw input (text, images, PDFs, screenshots) into
validated, Enterprise Architect 17.1-importable XMI artefacts via a mandatory canonical JSON
intermediate model.

Package: `ea_mbse_pipeline` (src-layout under `src/`)

---

## Commands

```bash
# First-time setup
pip install uv
uv sync --extra dev

# Run all tests
pytest

# Fast unit tests only
pytest -m unit

# Single test file
pytest tests/unit/test_canonical_models.py -v

# Coverage
pytest --cov=ea_mbse_pipeline --cov-report=html

# Lint
ruff check src tests

# Type-check
mypy src

# Pipeline CLI (placeholder until stages are implemented)
ea-mbse-pipeline --help
ea-ingest --help
ea-validate --help
ea-serialize --help
```

---

## Architecture

The pipeline is a **linear, stage-gated chain**. Every stage must complete
successfully before the next stage starts. No stage may bypass the canonical model.

```
Raw Input (text / image / PDF / screenshot)
    │
    ▼
┌─────────────┐
│   Ingest    │  src/ea_mbse_pipeline/ingest/
└──────┬──────┘
       │ RawContent
       ▼
┌─────────────────────────────────────────┐
│         Canonical Model (JSON)          │  src/ea_mbse_pipeline/canonical/
└────────────────────┬────────────────────┘
                     │  CanonicalModel
          ┌──────────┴──────────┐
          ▼                     ▼
  ┌──────────────┐     ┌──────────────────┐
  │  Retrieval   │     │   Validation     │  src/ea_mbse_pipeline/validation/
  │  (context/  │     │  (metamodel      │
  │   RAG)      │     │   rules)         │
  └──────┬───────┘     └───────┬──────────┘
         │                     │ ValidationReport
         └──────────┬──────────┘
                    ▼
          ┌──────────────────┐
          │  Serialization   │  src/ea_mbse_pipeline/serialization/
          └────────┬─────────┘
                   │ SerializedArtefact (XMI / CSV)
                   ▼
          ┌──────────────────┐
          │    EA Test       │  src/ea_mbse_pipeline/ea_test/
          │ (import + regr.) │
          └──────────────────┘

Cross-cutting:
  Metamodel   src/ea_mbse_pipeline/metamodel/     XMI → RuleSet
  Shared      src/ea_mbse_pipeline/shared/         errors, logging, provenance, types
  Orchestr.   src/ea_mbse_pipeline/orchestration/  PipelineOrchestrator (DI)
```

### Stage summary

| Stage | Module | Input | Output |
|---|---|---|---|
| Ingest | `ingest` | file path | `RawContent` |
| CanonicalBuilder | `canonical` | `RawContent` | `CanonicalModel` |
| MetamodelCompiler | `metamodel` | XMI path | `RuleSet` |
| Retrieval | `retrieval` | query + corpus | `RetrievalResult` |
| Validator | `validation` | `CanonicalModel` + `RuleSet` | `ValidationReport` |
| Serializer | `serialization` | `CanonicalModel` | `SerializedArtefact` |
| EA Test | `ea_test` | `SerializedArtefact` | `EATestReport` |
| Orchestrator | `orchestration` | config | `PipelineResult` |

---

## Non-negotiable engineering rules

### Canonical model is mandatory
Every pipeline run MUST pass through `CanonicalModel`. No stage may consume raw
input directly from a previous stage without going through the canonical model first.
The JSON Schema at `schemas/canonical_model.schema.json` is authoritative.
`src/ea_mbse_pipeline/canonical/models.py` must stay in sync with it.

### Metamodel XMI is normative
The metamodel XMI and its written description are the single source of truth for
what is valid. Rules derived from it override any other heuristic.

### Screenshots are supporting, never primary
Image/screenshot input may inform element extraction but must never be the sole
source of a canonical model element. Every element derived from an image must have
a corroborating text or metamodel reference in its `provenance`.

### No silent degradation
Serializers must fail loudly. If a canonical model element cannot be mapped to a
valid XMI construct, raise a typed `SerializationError` with an error code. Never
silently drop elements, default to placeholder values, or produce partial XMI.

### Every derivation must have provenance
Every `ModelElement`, `ModelRelationship`, and `ModelDiagram` in the canonical model
must carry a `provenance` field identifying its source (file path + chunk/page/line).
Use `shared.provenance.Provenance`.

### Error codes
All pipeline errors must carry a structured error code from `shared.errors.ErrorCode`.
Never raise bare `Exception` or `ValueError` in pipeline code.

### Python style
- Python ≥ 3.11. Use `StrEnum`, `match/case`, `X | Y` unions, `Self`.
- Full type annotations on every function. `mypy --strict` must pass.
- `logging.getLogger(__name__)` in every module. No `print()` in pipeline code.
- `raise NotImplementedError` in all stub method bodies (never bare `...` or `pass`).

### Architecture
- Each stage exposes a `Protocol` (structural) and a `BaseXxx(ABC)` in `protocols.py`.
- Each stage's data contract lives in `models.py` as Pydantic v2 models.
- `orchestration/` wires stages via constructor injection — no global singletons.
- `shared/` contains only cross-cutting utilities; no stage-specific logic.

### Testing
- Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.golden`.
- Unit tests must not touch the filesystem or network.
- Golden tests compare serialiser output byte-for-byte against `data/golden/`.
- Test-first where the contract is well-defined (models, validators, serialisers).

### Sprint discipline
Every sprint must deliver working, tested code — no "skeleton PRs" that only move
files around. If a stage is not ready, its entry point raises `NotImplementedError`
with a milestone reference.

---

## Data layout

```
data/raw/metamodel/     XMI metamodel files (normative input)
data/raw/screenshots/   Screenshot input (supporting only)
data/raw/corpus/        Text / PDF corpus documents
data/processed/         Intermediate artefacts (not committed by default)
data/fixtures/          Reusable test fixture data (committed)
data/golden/            Golden XMI/CSV artefacts for regression (committed)
outputs/                Pipeline run outputs (not committed)
```

---

## EA XMI conventions

See `.claude/rules/ea-xmi-conventions.md`. Key points:
- XMI 2.1, `xmi:version="2.1"`.
- Every element gets an EA-style GUID `{UUID}` (curly-brace-wrapped).
- Stereotypes via `<xmi:Extension extender="Enterprise Architect">`, not UML profile application.
- Root package must be named `EA_Model`.
- Use `lxml.etree` (not stdlib `xml`) for all XMI construction and parsing.

---

## .claude/ directory

| Path | Purpose |
|---|---|
| `.claude/rules/coding-standards.md` | Python conventions, typing, testing |
| `.claude/rules/ea-xmi-conventions.md` | EA 17.1 XMI format rules |
| `.claude/rules/data-governance.md` | Provenance, data tiers, golden files |
| `.claude/agents/metamodel-analyst.md` | Agent: analyse XMI, implement MetamodelCompiler |
| `.claude/agents/pipeline-debugger.md` | Agent: trace and fix pipeline failures |
| `.claude/agents/xmi-serializer.md` | Agent: implement and repair XMI serializer |
| `.claude/skills/validate-canonical.md` | Skill: validate a canonical model JSON |
| `.claude/skills/compile-metamodel.md` | Skill: compile XMI to RuleSet JSON |

---

## Note on ea_pipeline/

`src/ea_pipeline/` is an earlier iteration of this package. It is superseded by
`src/ea_mbse_pipeline/`. Do not add new code to `ea_pipeline/`.
