# ADR-001: Sprint 1a Cleanup — Package Naming, Canonical Layer, Serializer Strategy

**Date**: 2026-03-16
**Status**: Accepted
**Sprint**: 1a (pre-Sprint 2 hardening)

---

## Context

Sprint 1 established the project skeleton under two package names:
- `ea_pipeline` (original iteration, under `src/ea_pipeline/`)
- `ea_mbse_pipeline` (revised architecture, under `src/ea_mbse_pipeline/`)

Before Sprint 2 (ingestion implementation) can safely start, the following
ambiguities needed resolution:

1. Two Python packages with overlapping stage names caused import confusion.
2. The README and stage ordering in CLAUDE.md did not match the intended
   pipeline flow (retrieval before canonical, not after).
3. The `.claude/` agent layer was missing roles for Sprint 2 work.
4. `settings.local.json` only allowed `cd` — blocking normal development.
5. No documented decision record existed for architectural choices.

---

## Decisions

### 1. `ea_mbse_pipeline` is the sole Python package name

The legacy `src/ea_pipeline/` package has been removed. All imports, tests,
pyproject.toml configuration, and documentation reference only `ea_mbse_pipeline`.

**Why**: A single authoritative package name removes import confusion, prevents
test divergence, and makes the domain (MBSE) explicit. `ea_pipeline` was a
proof-of-concept iteration superseded by the more complete `ea_mbse_pipeline`.

### 2. Pipeline stage order corrected

The canonical pipeline order is:

```
ingest → metamodel compiler → retrieval/evidence → canonical model
      → validation → serialization → EA checks
```

The previous CLAUDE.md diagram incorrectly showed retrieval as a parallel
output of the canonical model rather than as evidence feeding into it.

**Why**: Evidence (retrieval) informs element extraction; it must be gathered
*before* the canonical model is built, not after.

### 3. Canonical model remains a mandatory pipeline stage

No stage may consume `RawContent` from a previous stage without first producing
a `CanonicalModel`. `schemas/canonical_model.schema.json` remains authoritative.

**Why**: The canonical model provides a stable, validated, schema-checked interface
between ingestion and all downstream stages. Bypassing it breaks provenance tracking,
validation portability, and serializer interchangeability.

### 4. Serializer target format kept open (pluggable)

`SerializationFormat` currently enumerates `XMI` and `CSV`, but the concrete
serializer implementation is not yet written. The architecture uses
`SerializerProtocol` (structural) and `BaseSerializer(ABC)` rather than
hard-wiring a format.

**Why**: Whether EA XMI 2.1 round-trips reliably through EA 17.1's importer for
*all* element types is still being validated. Committing to a single format before
this validation risks rework. The canonical model is the stable contract; serializer
plugins can be swapped.

### 5. `.claude/agents/` expanded with six pipeline-role agents

The following agents were added to support Sprint 2+ work:

| Agent | Sprint relevance |
|---|---|
| `corpus-ingester` | Sprint 2 — ingestion implementation |
| `metamodel-guardian` | Sprint 2 — metamodel XMI analysis |
| `evidence-retriever` | Sprint 2 — corpus RAG |
| `canonical-modeler` | Sprint 2/3 — canonical model building |
| `ea-serializer` | Sprint 3 — XMI/CSV serialization |
| `import-validator` | Sprint 4 — EA import checks |

The previous `metamodel-analyst` and `xmi-serializer` agents are superseded
by `metamodel-guardian` and `ea-serializer` respectively.

### 6. `.claude/skills/` renamed to `.claude/playbooks/`

Workflow guides (step-by-step operational procedures) are stored under
`.claude/playbooks/`. This name is more descriptive for documents that guide
*how* to perform a multi-step workflow rather than defining a reusable code snippet.

Six playbooks added:
- `ingest-kaderdocs`, `compile-metamodel`, `generate-canonical-model`,
  `validate-canonical`, `serialize-ea`, `run-import-validation`.

### 7. `settings.local.json` is environment-specific and gitignored

The file now allows common development operations (`pytest*`, `ruff*`, `mypy*`,
`uv*`, `python*`, `git status/log/diff/grep/show`). It is added to `.gitignore`
because shell permission preferences are machine-specific.

A `.claude/settings.local.json.example` template is committed for onboarding.

**Why**: The previous `allow: ["Bash(cd:*)"]` blocked all normal development
commands, requiring user confirmation for every `pytest` or `ruff` run — disruptive
in a Windows + VS Code + PowerShell workflow.

---

## Consequences

- Sprint 2 can begin with a single, unambiguous package target.
- `git grep 'ea_pipeline'` (excluding this ADR and .gitignore) returns zero matches.
- All `.claude/agents/` files follow a consistent structure:
  Purpose, Trigger, Input, Output, Behaviour, Constraints, Quality gates.
- All `.claude/playbooks/` files follow:
  Purpose, Input, Steps, Output, Quality gates.
