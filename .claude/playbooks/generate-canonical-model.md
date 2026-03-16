# Playbook: generate-canonical-model

## Purpose
Build a `CanonicalModel` JSON from one or more ingested source documents,
with retrieval evidence and metamodel constraints applied.

## Input
- A `RawContent` object (from the Ingest stage).
- A `RetrievalResult` (from the Retrieval stage — corpus evidence).
- A `RuleSet` (from the MetamodelCompiler — element type constraints).

## Steps
1. Confirm all inputs are available:
   - `RawContent` produced by `ea-ingest <source>`.
   - `RetrievalResult` produced by running retrieval queries for candidate elements.
   - `RuleSet` compiled from `data/raw/metamodel/`.
2. Run the `CanonicalBuilder`:
   ```python
   canonical_model = builder.build(raw_content, retrieval_result, rule_set)
   ```
3. Validate the output against the JSON Schema:
   ```
   /validate-canonical <path-to-canonical.json>
   ```
4. Review:
   - Every `ModelElement` has `provenance.sources` with at least one `SourceRef`.
   - Image-derived elements have a second corroborating `SourceRef`.
   - All `ModelRelationship.source_id` and `target_id` resolve to existing elements.
5. Save to `data/processed/<run-id>.canonical.json` for downstream stages.

## Output
- A `CanonicalModel` JSON that validates against `schemas/canonical_model.schema.json`.
- All elements carry `provenance` with non-empty `sources`.

## Quality gates
- `ValidationReport.passed == True` after running the Validator on the output.
- Zero elements with empty `provenance.sources`.
- No screenshot-derived element exists without a corroborating text/metamodel source.
- `schemas/canonical_model.schema.json` validation passes (jsonschema).
