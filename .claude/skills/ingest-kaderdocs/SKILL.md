---
name: ingest-kaderdocs
description: Ingest one or more framework documents (PDF, DOCX, text) from data/raw/corpus/ into SourceDocument + CorpusChunk records and verify the result is usable as evidence for the CanonicalBuilder.
---

# Skill: ingest-kaderdocs

Ingest framework documents from `data/raw/corpus/` and verify the resulting
`IngestRunManifest` is pipeline-ready.

## When to invoke

Use `/ingest-kaderdocs` when a new source document needs to enter the pipeline.
The skill ingests the entire corpus directory, so just place the file and run.

## Steps

### 1. Place the document

Copy the source file to `data/raw/corpus/<name>.<ext>`.

Supported types: `.pdf`, `.txt`, `.md`, `.rst`

### 2. Run the ingest stage

**Via CLI (recommended):**

```bash
ea-ingest \
  --corpus-dir data/raw/corpus \
  --metamodel-dir data/raw/metamodel \
  --screenshots-dir data/raw/screenshots \
  --output-dir data/processed/ingest
```

**Via the pipeline app:**

```bash
ea-mbse-pipeline ingest \
  --corpus-dir data/raw/corpus \
  --output-dir data/processed/ingest
```

**Via Python API (REPL / notebook):**

```python
from pathlib import Path
from ea_mbse_pipeline.ingest import IngestPipeline

pipeline = IngestPipeline(
    corpus_dir=Path("data/raw/corpus"),
    metamodel_dir=Path("data/raw/metamodel"),
    screenshots_dir=Path("data/raw/screenshots"),
    output_dir=Path("data/processed/ingest"),
)
manifest = pipeline.run()
print(f"run_id   : {manifest.run_id}")
print(f"docs     : {manifest.document_count}")
print(f"chunks   : {manifest.chunk_count}")
print(f"errors   : {manifest.errors}")
```

**Single-file ingest (lower-level):**

```python
from pathlib import Path
from ea_mbse_pipeline.ingest import build_ingestor

ingestor = build_ingestor()
raw = ingestor.ingest(Path("data/raw/corpus/<name>.<ext>"))
print(raw.model_dump_json(indent=2))
```

### 3. Verify the manifest

Inspect `data/processed/ingest/{run_id}/manifest.json`:

```python
import json
from pathlib import Path

manifest_path = Path(manifest.output_json_path)
data = json.loads(manifest_path.read_text())

assert data["errors"] == [], "Ingestion errors found"
assert data["document_count"] >= 1, "No documents ingested"
assert data["chunk_count"] >= 1, "No chunks produced"
```

Check that:
- `errors` is empty (or contains only expected file-skips)
- `source_documents` contains an entry for your file
- `chunks` are non-empty and contain coherent text
- Each chunk has `provenance_sources` pointing back to the source file

### 4. Spot-check chunks

```python
for chunk in manifest.chunks[:3]:
    print(chunk.section_title, "|", chunk.text[:120])
    print("  keywords:", chunk.detected_keywords)
    print("  provenance:", chunk.provenance_sources[0].file_path)
```

### 5. Query the SQLite database (optional)

```bash
sqlite3 data/processed/ingest/<run_id>/ingest.db \
  "SELECT section_title, char_count, detected_keywords FROM corpus_chunks LIMIT 10;"
```

## Quality gates

- `manifest.errors == []` — no file failed to ingest.
- `manifest.document_count >= 1` — at least one document was ingested.
- `manifest.chunk_count >= 1` — at least one chunk was produced.
- Every chunk has `provenance_sources` with a non-empty `file_path`.
- `manifest.json` and `ingest.db` exist in `data/processed/ingest/{run_id}/`.
- `RawContent.text` from single-file ingest contains coherent, un-garbled text.

## Output locations

```
data/processed/ingest/{run_id}/
  manifest.json   full IngestRunManifest
  chunks.json     CorpusChunk list (retrieval-ready)
  ingest.db       SQLite: ingest_runs, source_documents, corpus_chunks, image_assets
```

## Reference

Architecture: `docs/architecture/ingest.md`
Full workflow: `.claude/playbooks/ingest-kaderdocs.md`
