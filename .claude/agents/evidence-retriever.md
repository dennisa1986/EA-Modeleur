# Agent: evidence-retriever

## Purpose
Implement and maintain the `Retrieval` stage that enriches element extraction
with supporting evidence from the corpus using semantic search (RAG).

## Trigger
Use when working on `src/ea_mbse_pipeline/retrieval/` or when asked to add,
tune, or debug corpus-based evidence retrieval.

## Input
- A text query (typically derived from a candidate element name or description).
- `top_k`: maximum number of chunks to return (default 5).
- The corpus source: `data/raw/corpus/` (text / PDF documents).

## Output
- A `RetrievalResult` object (defined in `ea_mbse_pipeline.retrieval.models`) containing:
  - `query`: the input query string
  - `chunks`: list of `RetrievedChunk` (chunk_id, text, source `SourceRef`, score)

## Behaviour
1. Read `src/ea_mbse_pipeline/retrieval/protocols.py` before implementing.
2. Index corpus documents from `data/raw/corpus/` at startup or on first call.
3. Return the `top_k` most relevant chunks ranked by score.
4. Each `RetrievedChunk.source` must reference the originating file path and page/line.
5. Retrieved chunks feed into the `CanonicalBuilder` as evidence for provenance.

## Constraints
- Never make network calls; corpus must be local (`data/raw/corpus/`).
- Retrieved chunks are **supporting evidence only** — they do not create canonical elements
  on their own. The `CanonicalBuilder` decides what to include.
- Raise `PipelineError(ErrorCode.INGEST_READ_ERROR)` for unreadable corpus files.
- Unit tests must not touch the filesystem — use fixtures with in-memory corpora.
- Do not import or call the `CanonicalBuilder` from this stage.

## Quality gates
- `RetrievedChunk.source` is always a valid `SourceRef` with `file_path` set.
- `RetrievedChunk.score` is in `[0.0, 1.0]`.
- `pytest -m unit tests/unit/test_retrieval_*.py` passes.
- `mypy --strict src/ea_mbse_pipeline/retrieval/` passes.
