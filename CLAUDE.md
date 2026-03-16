# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Production-grade MBSE pipeline that transforms raw input (text, images, PDFs, screenshots) into
validated, Enterprise Architect 17.1-importable artefacts via a mandatory canonical JSON
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

# Pipeline CLI (stubs — stages not yet implemented)
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
Raw Input (text / image / PDF / screenshot)     Metamodel (XMI)
               │                                      │
               ▼                                      ▼
       ┌──────────────┐                   ┌──────────────────────┐
       │    Ingest    │  ingest/          │  MetamodelCompiler   │  metamodel/
       └──────┬───────┘                   └──────────┬───────────┘
              │ RawContent                            │ RuleSet
              │                                       │
              └──────────────┬────────────────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │  Retrieval / Evidence │  retrieval/
                 └───────────┬───────────┘
                             │ RetrievalResult
                             ▼
              ┌──────────────────────────────┐
              │      Canonical Model         │  canonical/
              │         (JSON)               │  schemas/canonical_model.schema.json
              └──────────────┬───────────────┘
                             │ CanonicalModel  ← MANDATORY — no stage bypasses this
                             ▼
                    ┌─────────────────┐
                    │   Validation    │  validation/
                    └────────┬────────┘
                             │ ValidationReport
                             ▼
                    ┌─────────────────┐
                    │  Serialization  │  serialization/  (pluggable SerializerProtocol)
                    └────────┬────────┘
                             │ SerializedArtefact
                             ▼
                    ┌─────────────────┐
                    │    EA Checks    │  ea_test/
                    └─────────────────┘

Cross-cutting:
  Shared      src/ea_mbse_pipeline/shared/         errors, logging, provenance, types
  Orchestr.   src/ea_mbse_pipeline/orchestration/  PipelineOrchestrator (DI)
```

### Stage summary

| Stage | Module | Input | Output |
|---|---|---|---|
| Ingest | `ea_mbse_pipeline.ingest` | file path | `RawContent` |
| MetamodelCompiler | `ea_mbse_pipeline.metamodel` | XMI path | `RuleSet` |
| Retrieval | `ea_mbse_pipeline.retrieval` | query + corpus | `RetrievalResult` |
| CanonicalBuilder | `ea_mbse_pipeline.canonical` | `RawContent` + evidence | `CanonicalModel` |
| Validator | `ea_mbse_pipeline.validation` | `CanonicalModel` + `RuleSet` | `ValidationReport` |
| Serializer | `ea_mbse_pipeline.serialization` | `CanonicalModel` | `SerializedArtefact` |
| EA Checks | `ea_mbse_pipeline.ea_test` | `SerializedArtefact` | `EATestReport` |
| Orchestrator | `ea_mbse_pipeline.orchestration` | config | `PipelineResult` |

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
valid serialized artefact, raise `PipelineError(ErrorCode.SERIAL_UNMAPPABLE_ELEMENT)`.
Never silently drop elements, default to placeholder values, or produce partial output.

### Every derivation must have provenance
Every `ModelElement`, `ModelRelationship`, and `ModelDiagram` in the canonical model
must carry a `provenance` field identifying its source (file path + chunk/page/line).
Use `ea_mbse_pipeline.shared.provenance.Provenance`.

### Error codes
All pipeline errors must carry a structured error code from
`ea_mbse_pipeline.shared.errors.ErrorCode`. Never raise bare `Exception` or `ValueError`
in pipeline code.

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

### Serializer target format
`SerializationFormat` enumerates `XMI` and `CSV` as candidates. The concrete format
for production is not yet locked — EA XMI 2.1 round-trip fidelity through EA 17.1 is
still being validated technically. Use `SerializerProtocol` for pluggable implementations.
See `.claude/rules/ea-xmi-conventions.md` for XMI-specific constraints.

### Testing
- Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.golden`.
- Unit tests must not touch the filesystem or network.
- Golden tests compare serializer output byte-for-byte against `data/golden/`.
- Test-first where the contract is well-defined (models, validators, serializers).

### Sprint discipline
Every sprint must deliver working, tested code — no "skeleton PRs" that only move
files around. If a stage is not ready, its entry point raises `NotImplementedError`
with a milestone reference.

---

## Data layout

```
data/raw/metamodel/     XMI metamodel files (normative input)
data/raw/screenshots/   Screenshot input (supporting only, not committed)
data/raw/corpus/        Text / PDF corpus documents
data/processed/         Intermediate artefacts (not committed)
data/fixtures/          Reusable test fixture data (committed)
data/golden/            Golden artefacts for regression (committed)
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

### Rules
| Path | Purpose |
|---|---|
| `.claude/rules/coding-standards.md` | Python conventions, typing, testing |
| `.claude/rules/ea-xmi-conventions.md` | EA 17.1 XMI format rules |
| `.claude/rules/data-governance.md` | Provenance, data tiers, golden files |

### Agents (pipeline roles)
| Path | Role |
|---|---|
| `.claude/agents/corpus-ingester.md` | Implement raw input ingestion stage |
| `.claude/agents/metamodel-guardian.md` | Analyse XMI, implement MetamodelCompiler |
| `.claude/agents/evidence-retriever.md` | Implement corpus RAG / retrieval stage |
| `.claude/agents/canonical-modeler.md` | Build and maintain CanonicalModel stage |
| `.claude/agents/ea-serializer.md` | Implement and repair serialization stage |
| `.claude/agents/import-validator.md` | Implement EA import checks / regression |
| `.claude/agents/pipeline-debugger.md` | Trace and fix pipeline failures |

### Skills (Claude-native invocation — use `/skill-name`)
Skills are invoked directly by Claude Code using `/skill-name`. They contain
concrete, executable instructions with code examples and quality gates.

| Path | Invocation | Purpose |
|---|---|---|
| `.claude/skills/ingest-kaderdocs/SKILL.md` | `/ingest-kaderdocs` | Ingest framework documents into corpus |
| `.claude/skills/compile-metamodel/SKILL.md` | `/compile-metamodel` | Compile XMI metamodel to RuleSet JSON |
| `.claude/skills/generate-canonical-model/SKILL.md` | `/generate-canonical-model` | Build a CanonicalModel from raw input |
| `.claude/skills/validate-canonical/SKILL.md` | `/validate-canonical` | Validate a CanonicalModel JSON |
| `.claude/skills/serialize-ea/SKILL.md` | `/serialize-ea` | Serialize a CanonicalModel to target format |
| `.claude/skills/run-import-validation/SKILL.md` | `/run-import-validation` | Run EA import checks on serialized output |

### Playbooks (human reference — extended workflow documentation)
Playbooks are step-by-step guides for human operators. They explain the *why*
behind each step, cover edge cases, and are consulted during onboarding or
troubleshooting. Skills derive their instructions from playbooks but are
self-contained.

| Path | Workflow |
|---|---|
| `.claude/playbooks/ingest-kaderdocs.md` | Ingest framework documents into corpus |
| `.claude/playbooks/compile-metamodel.md` | Compile XMI metamodel to RuleSet JSON |
| `.claude/playbooks/generate-canonical-model.md` | Build a CanonicalModel from raw input |
| `.claude/playbooks/validate-canonical.md` | Validate a CanonicalModel JSON |
| `.claude/playbooks/serialize-ea.md` | Serialize a CanonicalModel to target format |
| `.claude/playbooks/run-import-validation.md` | Run EA import checks on serialized output |
