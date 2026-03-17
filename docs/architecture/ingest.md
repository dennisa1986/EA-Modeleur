# Ingest Stage — Architecture Note

## Role in the pipeline

Stage 1 of the linear MBSE pipeline.  Converts raw input files into structured,
queryable artefacts that subsequent stages consume without touching the originals.

```
data/raw/corpus/       ──►  SourceDocument + CorpusChunk records
data/raw/metamodel/    ──►  xmi_files list  (passed to MetamodelCompiler)
data/raw/screenshots/  ──►  ImageAsset records

All outputs → data/processed/ingest/{run_id}/
```

## Responsibilities

| Responsibility | Module |
|---|---|
| File discovery (corpus, metamodel, screenshots) | `file_discovery.py` |
| PDF text extraction (per-page) | `pdf_extract.py` |
| Plain-text and PDF chunking by section / paragraph | `chunking.py` |
| Metadata attachment (keywords, provenance, IDs) | `metadata.py` |
| Screenshot / image manifest | `image_manifest.py` |
| JSON output (manifest + chunks) | `store_json.py` |
| SQLite persistence | `store_sqlite.py` |
| Orchestration of all of the above | `pipeline.py` |
| Single-file ingestor protocol implementations | `pipeline.py` |
| Data contracts | `models.py` |
| Stage interfaces (Protocol + ABC) | `protocols.py` |

## Data flow

```
IngestPipeline.run()
    │
    ├─ discover_metamodel_files()      ──► manifest.xmi_files  (list of str)
    │
    ├─ discover_corpus_files()
    │   └─ for each file:
    │       ├─ PDF  → extract_pdf() → chunk_pdf_pages() → build_corpus_chunk()
    │       └─ text → read_text()   → chunk_text()      → build_corpus_chunk()
    │       └─ → SourceDocument + []CorpusChunk
    │
    ├─ build_image_manifest()          ──► []ImageAsset
    │
    └─ save_manifest_json()            ──► manifest.json
       save_chunks_json()              ──► chunks.json
       save_to_sqlite()                ──► ingest.db
```

## Output structure

```
data/processed/ingest/
└── {run_id}/
    ├── manifest.json   — full IngestRunManifest (Pydantic model)
    ├── chunks.json     — { run_id, chunk_count, chunks: [...] }
    └── ingest.db       — SQLite: ingest_runs, source_documents,
                          corpus_chunks, image_assets
```

`run_id` is a UUID4 generated fresh on every `IngestPipeline.run()` call.

## Key data models

| Model | Description |
|---|---|
| `RawContent` | Single-file ingestor output — consumed directly by CanonicalBuilder |
| `SourceDocument` | File-level record: path, type, size, page count, metadata |
| `CorpusChunk` | Text excerpt: chunk_id, doc_id, page range, section, keywords, provenance |
| `ImageAsset` | Discovered image: path, dimensions, format |
| `IngestRunManifest` | Aggregates all of the above for one run |

Every `CorpusChunk` carries `provenance_sources: list[SourceRef]` so downstream
stages never need to guess the origin of a text excerpt.

## Chunking strategy

1. **Heading detection** — heuristic: numbered sections (`1.2 Title`), ALL CAPS
   short lines, or title-case lines without terminal sentence punctuation.
2. **PDF pages** — each heading starts a new chunk; text between headings is
   accumulated across lines.
3. **Plain text** — split on double newlines (paragraph boundaries), then check
   first line for heading.
4. **Overflow splitting** — chunks exceeding `_MAX_CHUNK_CHARS` (4 000) are split
   at paragraph, sentence, or hard-character boundaries.
5. **Minimum size** — candidates shorter than `_MIN_CHUNK_CHARS` (80) are discarded.

## File discovery

All three source directories are scanned by `file_discovery.py`.  Discovery is
**recursive by default** (`recursive=True`): files in subdirectories are
included and the result is sorted by full path for deterministic ordering.

Set `recursive=False` on `IngestPipeline` to limit discovery to the top-level
directory only:

```python
pipeline = IngestPipeline(
    corpus_dir=Path("data/raw/corpus"),
    ...
    recursive=False,
)
```

## Document ID strategy

`doc_id_from_path(path)` produces a stable `"doc-<16 hex>"` identifier for
each source file.

**Strategy (Sprint 2a):** `SHA-256(<filename_bytes> + b":" + <first 64 KiB of
content>)`, truncated to 16 hex characters.

- **Collision-resistant:** same name + different content → different ID; same
  content + different name → different ID.
- **Stable:** re-ingesting the same file always produces the same `doc_id`,
  enabling idempotent upserts in SQLite.
- **Fast:** reads at most 64 KiB regardless of file size.
- **Fallback:** if the file is unreadable (e.g. missing), degrades to
  `SHA-256(<filename>:<stat.st_size>)` and logs a debug message.

Note: two files with identical names *and* identical first 64 KiB are
considered the same document and receive the same `doc_id`.  This is an
intentional design choice — same content is the same source.

## Limitations of this implementation

- **No OCR** — image-only PDFs (scanned documents) yield `INGEST_EMPTY_CONTENT`.
  Add an OCR adapter (e.g. `pytesseract`) as a fallback in a later sprint.
- **No DOCX / PPTX** — only `.pdf`, `.txt`, `.md`, `.rst` are ingested from the
  corpus.  Add `python-docx` / `python-pptx` adapters if required.
- **No semantic chunking** — the chunker is purely syntactic (headings + blank
  lines).  A sentence-transformer-based splitter would improve retrieval quality
  but is out of scope until retrieval stage design is finalised.
- **No deduplication** — the same file ingested twice produces a new run_id but
  reuses the same deterministic `doc_id`, enabling upsert semantics in SQLite.
- **Screenshots not OCR-d** — `ImageAsset` records are manifested but text is
  not extracted.  Screenshots are supporting input only (data-governance.md).
- **64 KiB fingerprint boundary** — two files with the same name and identical
  first 64 KiB but different content beyond that will share a `doc_id`.  In
  practice this does not arise with real documents.

## Extension points

| Need | Where to extend |
|---|---|
| New file format (DOCX, HTML) | Subclass `BaseIngestor`, register in `DispatchIngestor.__init__` |
| Richer chunking (semantic) | Add a new strategy to `chunking.py`; pass as parameter to `IngestPipeline` |
| Domain-specific keyword taxonomy | Extend `metadata.extract_keywords` or inject a domain-keyword classifier |
| OCR fallback for image PDFs | Add `ocr_pdf()` in `pdf_extract.py`, called when `full_text` is empty |
| Corpus pre-processing (normalisation, dedup) | Add a pre-processing step in `IngestPipeline._ingest_corpus_file` |

## Relation to the next stage (Retrieval / Evidence)

The retrieval stage reads `CorpusChunk` records from `chunks.json` or `ingest.db`
and builds a search index (keyword-based or vector-based) over the `text` field.

The `provenance_sources` field on every `CorpusChunk` is the primary bridge:
when the retrieval stage returns evidence to the `CanonicalBuilder`, it forwards
`provenance_sources` directly into the `Provenance` object on each `ModelElement`,
satisfying the "every derivation must have provenance" rule without re-reading
the original files.

The `xmi_files` list in `IngestRunManifest` is passed directly to the
`MetamodelCompiler` stage as input paths.
