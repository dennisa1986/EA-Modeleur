# Playbook: ingest-kaderdocs

## Purpose

Ingest one or more framework documents (PDF, text) from `data/raw/corpus/` into
structured `SourceDocument` and `CorpusChunk` records, persist them to JSON and
SQLite, and verify the output is ready for the retrieval and canonical modelling
stages.

## Input

| Source | Expected location | Types |
|---|---|---|
| Corpus documents | `data/raw/corpus/` | `.pdf`, `.txt`, `.md`, `.rst` |
| XMI metamodels | `data/raw/metamodel/` | `.xmi`, `.xml` |
| Screenshots (optional) | `data/raw/screenshots/` | `.png`, `.jpg`, … |

## Output

```
data/processed/ingest/{run_id}/
  manifest.json   — IngestRunManifest (all fields)
  chunks.json     — CorpusChunk list (used by retrieval stage)
  ingest.db       — SQLite with four tables
```

`run_id` is a fresh UUID4 per run.

## Steps

### 1. Place source documents

Copy documents to `data/raw/corpus/<name>.<ext>`.  Subdirectories are
supported — discovery is recursive by default, so
`data/raw/corpus/domain1/doc.pdf` is picked up automatically.

### 2. Run the ingest stage

```bash
# Preferred: installed CLI entry point
ea-ingest \
  --corpus-dir data/raw/corpus \
  --metamodel-dir data/raw/metamodel \
  --screenshots-dir data/raw/screenshots \
  --output-dir data/processed/ingest

# Alternative: script
python scripts/run_ingest.py \
  --corpus-dir data/raw/corpus \
  --output-dir data/processed/ingest
```

Exit code 0 = success.  Exit code 1 = partial failure (some files errored).

### 3. Inspect the manifest

Open `data/processed/ingest/{run_id}/manifest.json`.  Key fields to check:

| Field | Expected value |
|---|---|
| `errors` | `[]` (empty list) |
| `document_count` | ≥ 1 |
| `chunk_count` | ≥ 1 per document |
| `xmi_files` | lists all `.xmi` files from metamodel dir |
| `output_json_path` | non-null, file exists |
| `output_sqlite_path` | non-null, file exists |

### 4. Spot-check chunk quality

```python
import json
from pathlib import Path

data = json.loads(Path("data/processed/ingest/<run_id>/chunks.json").read_text())
for c in data["chunks"][:5]:
    print(c["section_title"], "|", c["text"][:100])
    print("  keywords:", c["detected_keywords"])
    print("  page:", c["page_start"])
```

Verify:
- Text is coherent (not garbled encoding).
- `section_title` is populated where the source has headings.
- `detected_keywords` are domain-relevant terms.
- `provenance_sources` traces back to the correct source file.

### 5. Query the SQLite database (optional)

```bash
sqlite3 data/processed/ingest/<run_id>/ingest.db <<EOF
SELECT d.file_name, COUNT(c.chunk_id) AS chunks
FROM source_documents d
JOIN corpus_chunks c ON c.doc_id = d.doc_id
GROUP BY d.file_name;
EOF
```

### 6. Hand off to retrieval stage

The retrieval stage loads `chunks.json` (or queries `corpus_chunks` in `ingest.db`)
to build its search index.  Pass the `run_id` or the manifest path as configuration.

## Quality gates

- `manifest.errors == []` — no ingestion failures.
- Every `CorpusChunk.provenance_sources` has at least one `SourceRef` with a valid `file_path`.
- `manifest.json` and `ingest.db` are present and non-empty in the output directory.
- No `PipelineError` raised during the run (exit code 0).
- `RawContent.text` (from single-file ingest) contains coherent text.

## Limitations

- Image-only PDFs (no embedded text layer) raise `INGEST_EMPTY_CONTENT`.
  Workaround: provide a text-layer PDF, or add OCR support in a later sprint.
- DOCX and PPTX are not yet supported.  Add `python-docx` adapter when needed.
- Screenshots are manifested but not OCR-d; they are supporting input only.

## Architecture reference

`docs/architecture/ingest.md` — detailed data flow, extension points, and
design decisions for the ingest stage.
