---
name: ingest-kaderdocs
description: Ingest one or more framework documents (PDF, DOCX, text) from data/raw/corpus/ into a RawContent object and verify the result is usable as evidence for the CanonicalBuilder.
---

# Skill: ingest-kaderdocs

Ingest framework documents from `data/raw/corpus/` and verify the resulting `RawContent` is
pipeline-ready.

## When to invoke

Use `/ingest-kaderdocs` when a new source document needs to enter the pipeline.
Supply the file path as an argument:

```
/ingest-kaderdocs data/raw/corpus/<name>.<ext>
```

## Steps

1. **Confirm the file exists** at `data/raw/corpus/<name>.<ext>`.
   - If it is missing, tell the user to place the file there first.

2. **Run the Ingest CLI**:
   ```bash
   ea-ingest data/raw/corpus/<name>.<ext>
   ```
   Or call the Python API directly:
   ```python
   from pathlib import Path
   from ea_mbse_pipeline.ingest import build_ingestor

   ingestor = build_ingestor()
   raw = ingestor.ingest(Path("data/raw/corpus/<name>.<ext>"))
   print(raw.model_dump_json(indent=2))
   ```

3. **Verify `RawContent`**:
   - `raw.kind` matches the expected `InputKind` (TEXT, PDF, IMAGE, etc.).
   - `raw.text` is non-empty for text/PDF inputs.
   - `raw.image_paths` is populated for image inputs.
   - `raw.source` resolves to the original file path.

4. **Spot-check extracted text** for encoding artefacts or truncation.

5. **If corpus retrieval is needed**, confirm the document is indexed:
   ```python
   from ea_mbse_pipeline.retrieval import build_retriever
   results = retriever.retrieve("sample keyword from the document")
   assert any(str(raw.source) in r.source_ref for r in results)
   ```

## Quality gates

- No `PipelineError` raised during ingestion.
- `RawContent.source` resolves to an existing path.
- `RawContent.text` contains coherent text (not garbled encoding).
- Document is retrievable via a keyword query after indexing.

## Reference

Full workflow context: `.claude/playbooks/ingest-kaderdocs.md`
