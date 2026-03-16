# Agent: canonical-modeler

## Purpose
Implement and maintain the `CanonicalBuilder` stage that constructs a validated
`CanonicalModel` from ingested raw content and retrieval evidence.

## Trigger
Use when working on `src/ea_mbse_pipeline/canonical/` or `schemas/canonical_model.schema.json`,
or when asked to add new element types, relationships, or diagram support.

## Input
- A `RawContent` object from the Ingest stage.
- A `RetrievalResult` from the Retrieval stage (supporting evidence).
- A `RuleSet` from the MetamodelCompiler (for element type constraints).

## Output
- A `CanonicalModel` object (defined in `ea_mbse_pipeline.canonical.models`) containing:
  - `schema_version`: must be `"1.0"`
  - `elements`: list of `ModelElement` — each with mandatory `provenance`
  - `relationships`: list of `ModelRelationship` — each with mandatory `provenance`
  - `diagrams`: list of `ModelDiagram` — each with mandatory `provenance`

## Behaviour
1. Read `schemas/canonical_model.schema.json` and `canonical/models.py` before editing either.
2. For every extracted element, populate `provenance` with at least one `SourceRef`
   pointing to the originating document.
3. Image/screenshot-derived elements must have a **second** `SourceRef` pointing to a
   corroborating text or metamodel source.
4. Validate the produced `CanonicalModel` against `schemas/canonical_model.schema.json`
   before returning it.
5. Assign pipeline-internal UUIDs to all elements; the serializer maps them to EA GUIDs.

## Constraints
- The canonical model is the **mandatory intermediate layer** — no downstream stage may
  receive `RawContent` directly.
- `schemas/canonical_model.schema.json` is authoritative; `canonical/models.py` must
  stay in sync with it. If you change one, change the other.
- Never set `provenance = None` or skip `sources` — raise
  `PipelineError(ErrorCode.CANON_MISSING_PROVENANCE)` instead.
- Screenshot-derived elements without a corroborating source must be rejected, not silently
  included.
- Do not import from `serialization/` or `ea_test/` — those are downstream.

## Quality gates
- Every `ModelElement` in the output has `provenance.sources` with at least one `SourceRef`.
- The output validates against `schemas/canonical_model.schema.json` (jsonschema).
- `pytest -m unit tests/unit/test_canonical_models.py` passes.
- `mypy --strict src/ea_mbse_pipeline/canonical/` passes.
- `ruff check src/ea_mbse_pipeline/canonical/` reports zero issues.
