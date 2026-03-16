# Playbook: ingest-kaderdocs

## Purpose
Ingest one or more framework documents (PDF, DOCX, text) from `data/raw/corpus/`
into a form the pipeline can process, and verify the ingested content is usable
as evidence for the `CanonicalBuilder`.

## Input
- One or more document files placed in `data/raw/corpus/`.
- `InputKind` hint (optional — auto-detected from extension).

## Steps
1. Place the source document in `data/raw/corpus/<name>.<ext>`.
2. Run the Ingest stage:
   ```
   ea-ingest <path-to-document>
   ```
   (or call `BaseIngestor.ingest(Path(...))` directly in a REPL / test).
3. Inspect the returned `RawContent`:
   - Confirm `kind` matches the expected `InputKind`.
   - Confirm `text` is non-empty for text/PDF documents.
   - Confirm `image_paths` is populated for image inputs.
4. Spot-check extracted text for truncation or encoding issues.
5. If the document will be used for retrieval, verify it appears in the corpus index
   by running a sample query through `BaseRetriever.retrieve()`.

## Output
- A valid `RawContent` object ready to be passed to the `CanonicalBuilder`.
- Confirmation that the document is indexed for retrieval (if applicable).

## Quality gates
- `RawContent.source` resolves to an existing file path.
- `RawContent.text` contains coherent text (not garbled encoding).
- No `PipelineError` raised during ingestion.
- Document retrievable via a keyword query after indexing.
