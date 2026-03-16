---
name: generate-canonical-model
description: Build a CanonicalModel JSON from ingested source documents, retrieval evidence, and metamodel constraints. Produces the mandatory intermediate artefact for all downstream stages.
---

# Skill: generate-canonical-model

Build a `CanonicalModel` JSON that satisfies `schemas/canonical_model.schema.json` and is
ready for the Validator.

## When to invoke

Use `/generate-canonical-model` when all upstream inputs are ready:
- A `RawContent` from the Ingest stage.
- A `RetrievalResult` from the Retrieval stage.
- A `RuleSet` from the MetamodelCompiler.

## Steps

1. **Confirm upstream outputs are available**:
   - `RawContent` — produced by `/ingest-kaderdocs`.
   - `RetrievalResult` — produced by the retriever for the relevant queries.
   - `RuleSet` — produced by `/compile-metamodel`.

2. **Run the CanonicalBuilder**:
   ```python
   from ea_mbse_pipeline.canonical import build_canonical_builder

   builder = build_canonical_builder()
   canonical = builder.build(raw_content, retrieval_result, rule_set)
   ```

3. **Save the result**:
   ```python
   from pathlib import Path
   import uuid

   run_id = uuid.uuid4().hex[:8]
   out = Path(f"data/processed/{run_id}.canonical.json")
   out.write_text(canonical.model_dump_json(indent=2))
   print(f"Saved to {out}")
   ```

4. **Validate against JSON Schema**:
   ```bash
   /validate-canonical data/processed/<run-id>.canonical.json
   ```

5. **Review provenance**:
   - Every `ModelElement` must have `provenance.sources` with ≥ 1 `SourceRef`.
   - Image-derived elements must have a corroborating text or metamodel `SourceRef`.
   - All `ModelRelationship.source_id` and `target_id` must resolve to existing element IDs.

## Quality gates

- `ValidationReport.passed == True` after running the Validator.
- Zero elements with empty `provenance.sources`.
- No screenshot-derived element without a corroborating text/metamodel source.
- `schemas/canonical_model.schema.json` validation passes (jsonschema).

## Reference

Full workflow context: `.claude/playbooks/generate-canonical-model.md`
