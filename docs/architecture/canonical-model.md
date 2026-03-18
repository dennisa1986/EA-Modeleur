# Canonical Model — Architecture

**Sprint 4 — 2026-03-17**

## Purpose

The canonical model is the **mandatory intermediate representation** in the EA MBSE pipeline.
Every pipeline run must pass through it.  No stage may consume raw input directly from a
previous stage without first materialising a `CanonicalModel`.

The JSON Schema at `schemas/canonical_model.schema.json` is authoritative.
Pydantic models in `src/ea_mbse_pipeline/canonical/models.py` and companion modules must stay
in sync with it.

---

## Module Layout

```
src/ea_mbse_pipeline/canonical/
├── __init__.py           — public API re-exports
├── models.py             — core artefacts (Package, Element, Relationship, …)
├── diagram_models.py     — ModelDiagram, DiagramObject, ElementBounds
├── evidence_models.py    — EvidenceLink
├── uncertainty_models.py — Uncertainty, UncertaintyLevel, UncertaintyType
├── ids.py                — ID generation and EA GUID conversion
├── builders.py           — CanonicalModelBuilder fluent API
├── io.py                 — JSON load/save with schema validation
└── protocols.py          — CanonicalBuilderProtocol, BaseCanonicalBuilder
```

---

## First-Class Artefacts

### CanonicalModel (root container)

The root object.  All stage outputs and inputs reference it as a whole.

| Field              | Type                       | Purpose |
|--------------------|----------------------------|---------|
| `schema_version`   | `str`                      | Schema version string (currently `"1.0"`) |
| `source_description` | `str`                   | Human-readable description of the source |
| `packages`         | `list[Package]`            | Package hierarchy |
| `elements`         | `list[ModelElement]`       | UML/SysML elements |
| `relationships`    | `list[ModelRelationship]`  | Directed connectors |
| `diagrams`         | `list[ModelDiagram]`       | Named EA diagrams with element placements |
| `requirement_links`| `list[RequirementLink]`    | SysML traceability links |
| `evidence_links`   | `list[EvidenceLink]`       | Retrieval evidence per artefact |
| `uncertainties`    | `list[Uncertainty]`        | Recorded derivation uncertainties |

### Package

Represents an EA package.  Packages form a tree via `parent_id`.
`parent_id = None` marks a root package.

`path` is a derived dot-notation string (e.g. `"Root.Domain.Sub"`).
It is populated at build time as a hint; the serializer recomputes it from
the parent chain.  Do not use `path` as a primary key.

### ModelElement

A first-class UML/SysML element (Class, Component, Block, Requirement, …).

`package_id` references the containing `Package` by ID.  `None` means the
element is at the model root.

`attributes` and `operations` are **typed** (`list[Attribute]` and
`list[Operation]` respectively) — no more `list[dict]`.

`tagged_values` is `list[TaggedValue]` — no more `dict[str, str]`.

### ModelRelationship

A directed connector between two `ModelElement`s.
`source_id` and `target_id` reference `ModelElement.id`.

### RequirementLink

A typed SysML traceability link.  `link_type` is one of:
`derives`, `satisfies`, `verifies`, `refines`, `traces`.

Both `source_id` and `target_id` may reference any artefact with an `id` field.

### ModelDiagram

A named EA diagram.  Contains `DiagramObject` entries — one per element placed on
the diagram.  `package_id` references the containing `Package`.

### DiagramObject

Links a `ModelElement` (or `Package`) to a diagram.
Carries an optional `ElementBounds` with `(x, y, width, height)` in EA pixel
coordinates for use by the serializer.  All other pipeline stages ignore bounds.

### EvidenceLink

Records which source chunk supports a canonical artefact.
`element_id` may reference any first-class artefact.
`relevance_score` is a float in `[0.0, 1.0]` provided by the retrieval stage.
`excerpt` contains a verbatim snippet from the source.

### Uncertainty

Records a derivation uncertainty on a canonical artefact.
`uncertainty_type` classifies the kind of uncertainty
(`extraction`, `classification`, `relationship`, `provenance`, `completeness`).
`level` indicates severity (`low`, `medium`, `high`).
The Validator can be configured to reject elements above a threshold.

---

## ID Strategy

### Pipeline-internal IDs

Every artefact carries an `id` field — a plain lowercase UUID4 string:

```
"3fa85f64-5717-4562-b3fc-2c963f66afa6"
```

- Assigned at creation time (via `canonical.ids.new_id()`).
- Never derived from names or external sources.
- Stable within a pipeline run and across reruns if the same builder code runs
  with explicit IDs.

### EA GUIDs

EA 17.1 requires `{UPPER-UUID}` format in XMI.
The serializer converts pipeline-internal IDs using `ids.to_ea_guid()`:

```python
to_ea_guid("3fa85f64-5717-4562-b3fc-2c963f66afa6")
# → "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"
```

`ModelElement.ea_guid` is populated **only** when ingesting a pre-existing EA
export that already contains GUIDs.  For new elements, leave it `None`.

---

## Provenance Contract

Every first-class artefact carries a mandatory `provenance: Provenance` field.

```python
class Provenance(BaseModel):
    sources: list[SourceRef]         # ≥1 source reference
    derivation_method: str           # e.g. "text-extraction", "ocr", "rule-R-001"
    confidence: float | None         # [0.0, 1.0], AI-derived elements only
    notes: str
```

Rules:
1. `sources` must contain at least one `SourceRef` pointing to a file in `data/raw/` or `data/fixtures/`.
2. Elements with `derivation_method == "ocr"` or `"image-extraction"` must have a **second** `SourceRef` pointing to a corroborating text or metamodel source.
3. The JSON Schema enforces `"minItems": 1` on `sources`.

Sub-element models (`Attribute`, `Operation`, `TaggedValue`, `Parameter`,
`DiagramObject`) do **not** carry provenance — their provenance is inherited from
the owning artefact.

---

## Relation to the Metamodel

The metamodel XMI (in `data/raw/metamodel/`) defines which element kinds,
relationship types, and stereotype combinations are valid for the target domain.
The `MetamodelCompiler` produces a `RuleSet` from the XMI.

The `Validator` cross-checks the `CanonicalModel` against the `RuleSet`.  The
canonical layer itself enforces only the structural contract (correct types,
mandatory provenance, valid enum values).  Domain-specific rules live in the
`RuleSet`, not in the Pydantic models.

`ElementKind` and `RelationshipKind` in the canonical model are intentionally
broader than any single metamodel — they cover UML + SysML basics.  The Validator
will reject elements whose `kind` is not present in the active `RuleSet`.

---

## Why This Model Is Sufficient for Validation and Serialization

| Stage | What it needs |
|-------|--------------|
| Validator | `elements`, `relationships`, `packages`, `requirement_links`, plus `provenance` on each for traceability checking |
| EA Serializer | `packages` (for nested `packagedElement` hierarchy), `elements` with typed `attributes`/`operations`, `relationships`, `diagrams` with `objects` and `bounds`, EA GUIDs via `ids.to_ea_guid()` |
| EA Test / Golden | Full `CanonicalModel` for byte-exact comparison of serializer output |

---

## Builder API

The `CanonicalModelBuilder` provides a fluent interface for constructing models
incrementally.  All `add_*` methods return `Self` for chaining:

```python
from ea_mbse_pipeline.canonical import CanonicalModelBuilder, ElementKind, new_id
from ea_mbse_pipeline.shared.provenance import Provenance, SourceRef

prov = Provenance(
    sources=[SourceRef(file_path="data/raw/corpus/spec.pdf", page=5)],
    derivation_method="text-extraction",
)

pkg_id = new_id()
model = (
    CanonicalModelBuilder(source_description="System spec")
    .add_package(id=pkg_id, name="Domain", provenance=prov)
    .add_element(kind=ElementKind.CLASS, name="Sensor", package_id=pkg_id, provenance=prov)
    .build()
)
```

`add_diagram` returns the new diagram's `id` (not `Self`) so it can be passed
immediately to `add_diagram_object`:

```python
diag_id = builder.add_diagram(name="Overview", diagram_type="Logical", provenance=prov)
builder.add_diagram_object(diagram_id=diag_id, element_id=sensor_id)
```

---

## I/O

```python
from ea_mbse_pipeline.canonical import load_canonical_model, save_canonical_model

model = load_canonical_model(Path("data/processed/model.json"))
save_canonical_model(model, Path("outputs/run-01/model.json"))
```

Both helpers validate against the JSON Schema.  `save_canonical_model` uses
`exclude_none=True` to keep the output clean (no `null` entries for optional
fields).

---

## Open Points for Sprint 5 / 6

| # | Topic | Notes |
|---|-------|-------|
| 1 | **Referential integrity enforcement at build time** | Currently only verified in tests. Consider a `CanonicalModel.check_integrity()` method that raises `CANONICAL_DANGLING_REFERENCE` for broken refs. |
| 2 | **Package path derivation** | `Package.path` is currently a hint set by the builder. Sprint 6 serializer should recompute it from the parent chain at serialization time. |
| 3 | **EA diagram connector serialization** | `ModelRelationship` entries placed on a diagram need a `DiagramConnector` equivalent (source/target anchor points). Currently deferred. |
| 4 | **`ea_guid` stability across runs** | If re-ingesting an EA export, the pipeline must detect existing GUIDs and preserve them. Needs a merge/reconcile step. |
| 5 | **Validator integration** | The `Validator` stage must consume both `CanonicalModel` and `RuleSet`. The canonical layer's `RequirementLink` types need to match the metamodel's constraint vocabulary. |
| 6 | **Uncertainty threshold config** | Configurable `max_uncertainty_level` in pipeline settings; the Validator rejects elements above this threshold. |
| 7 | **Schema version migration** | If schema advances to `"1.1"`, a migration helper is needed. Add a `CANONICAL_SCHEMA_VERSION_MISMATCH` error code. |
