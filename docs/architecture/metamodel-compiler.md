# Metamodel Compiler — Architecture

Sprint 3 delivery.

---

## Responsibilities

The metamodel compiler (Stage 2) transforms one or more normative XMI files
and optional supplementary description documents into a **machine-enforceable
constraint registry** (a `RuleSet`) that later stages — in particular the
Validator — can evaluate against a `CanonicalModel`.

Concretely the compiler:
1. Parses the XMI file and extracts element types, connectors, stereotypes,
   packages, and tagged-value schemas.
2. Optionally reads a plain-text or Markdown description file and extracts
   additional constraints that cannot be encoded in XMI alone.
3. Assembles all extracted constraints into a typed `RuleRegistry`.
4. Serialises the registry to a JSON file and a Markdown validation report.

The compiler does **not** build a `CanonicalModel`, validate one, or produce
serialised EA artefacts.  Those responsibilities belong to later stages.

---

## Module layout

```
src/ea_mbse_pipeline/metamodel/
├── __init__.py            Public API: MetamodelCompiler, RuleSet, RuleKind, …
├── compiler.py            Orchestrator — entry point for all callers
├── xmi_parser.py          lxml-based XMI parser → XMIParseResult
├── description_parser.py  Text/Markdown parser → DescriptionParseResult
├── provenance.py          Helpers: provenance_from_xmi / provenance_from_description
├── rule_registry.py       In-memory indexed store (RuleRegistry)
├── registry_export.py     JSON + Markdown export (RegistryExporter)
├── models.py              Pydantic data contracts (MetamodelRule, RuleSet, …)
└── protocols.py           Protocols + ABCs for each component
```

---

## Input / output contracts

### Inputs

| Source | Format | Role |
|---|---|---|
| `data/raw/metamodel/*.xmi` | XMI 2.1 (EA 17.1 export) | Normative |
| `data/raw/metamodel/description.txt` | Plain text / Markdown | Supplementary normative |

The XMI file is always required.  The description file is optional but
strongly recommended — many constraints (naming rules, forbidden patterns,
package placement) cannot be derived from XMI structure alone.

### Outputs

| File | Location | Purpose |
|---|---|---|
| `<stem>_registry.json` | `data/processed/metamodel/` | Machine-readable rule registry consumed by Validator |
| `<stem>_report.md` | `data/processed/metamodel/` | Human-readable validation report |

The default output directory is `settings.processed_dir / "metamodel"`.
Pass `--output-dir` to the script to override.

---

## Data flow

```
XMI file ──► XMIParser ──► XMIParseResult
                                │
Description file ──► DescriptionParser ──► DescriptionParseResult
                                │
            ┌───────────────────┘
            ▼
       MetamodelCompiler._rules_from_xmi()
       MetamodelCompiler._rules_from_description()
            │
            ▼
       RuleRegistry (in-memory, indexed)
            │
       ┌────┴────┐
       ▼         ▼
  RuleSet    RegistryExporter
  (JSON)     (Markdown)
```

---

## Rule model

Each `MetamodelRule` carries:

| Field | Purpose |
|---|---|
| `id` | Unique sequential ID, e.g. `R-CONN-001` |
| `kind` | `RuleKind` — what aspect the rule governs |
| `scope` | `RuleScope` — element / relationship / diagram / package / model |
| `description` | Human-readable rule statement |
| `constraint` | Optional JSON-Path / OCL expression for the Validator |
| `severity` | `error` (halts pipeline) or `warning` |
| `source_xmi_ref` | XPath locator into the source XMI |
| `provenance` | `shared.provenance.Provenance` — where the rule was derived from |
| `connector_constraint` | Typed: allowed connector type + source/target types |
| `tagged_value_constraint` | Typed: required tag name, pattern, applies-to |
| `naming_constraint` | Typed: regex pattern + applies-to |
| `package_placement` | Typed: allowed/forbidden package paths |
| `diagram_constraint` | Typed: diagram type + allowed/forbidden element types |
| `forbidden_pattern` | Typed: forbidden element/stereotype/connector combination |

Rules derived from XMI always have `provenance` set.  Rules derived from the
description file carry a `Provenance` with two `SourceRef` objects: the
description line and the corroborating XMI file.

---

## Provenance

Every rule must be traceable to its normative source.  The
`metamodel.provenance` module provides two helper functions that construct
`shared.provenance.Provenance` objects:

- `provenance_from_xmi(xmi_path, xmi_ref)` — for XMI-derived rules.  The
  `xmi_ref` is an XPath-style locator such as `//Class[@xmi:id='_cls_001']`.
- `provenance_from_description(desc_path, line, section, corroborating_xmi)`
  — for description-derived rules.  Includes a second `SourceRef` pointing to
  the XMI as corroborating evidence.

The `Provenance.derivation_method` is `"xmi-extraction"` or
`"description-extraction"` respectively.

---

## How the Validator uses the registry

The Validator will receive a `RuleSet` (loaded from JSON or passed directly).
It rebuilds a `RuleRegistry` with `RuleRegistry.from_rule_set(rule_set)` and
then queries it:

```python
registry = RuleRegistry.from_rule_set(rule_set)

# All connector rules
connector_rules = registry.by_kind(RuleKind.CONNECTOR)

# All element-level rules
element_rules = registry.by_scope(RuleScope.ELEMENT)

# Error rules only
blockers = registry.error_rules()
```

Each rule's `constraint` field (JSON-Path / OCL) can be evaluated against
`CanonicalModel` instances.  Typed sub-models (`connector_constraint`,
`tagged_value_constraint`, etc.) give the Validator richer structured data
than the raw constraint string alone.

---

## Limitations and extension points (Sprint 3 first iteration)

| Area | Current state | Extension path |
|---|---|---|
| Description parser classification | Best-effort keyword matching | Replace with a proper NLP classifier or structured rule format |
| Connector source/target resolution | Resolves by xmi:idref; may miss indirect references | Add a two-pass resolver that follows all idref chains |
| Diagram rules | Model defined; no XMI extraction yet | Implement when EA XMI diagram export format is confirmed |
| Package placement extraction | Extracted from Package elements; nesting depth not tracked | Add parent-tracking in `_parse_packages` |
| Naming patterns | Only extracted from description; not inferred from XMI conventions | Add XMI tagged-value annotation support |
| Stereotype base-type resolution | Names captured; base-type inheritance not resolved | Add inheritance traversal in `_parse_stereotypes` |
| OCL / JSON-Path constraint evaluation | Constraint strings stored but not evaluated | Implement evaluator in the Validator stage |
| Multi-XMI compilation | Single XMI per run | Add `compile_many()` that merges multiple XMI registries |
