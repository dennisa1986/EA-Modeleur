# Agent: corpus-ingester

## Purpose
Implement and maintain the `Ingest` stage that converts raw input files (text, PDF,
image, screenshot) into validated `RawContent` objects.

## Trigger
Use when working on `src/ea_mbse_pipeline/ingest/` or when asked to add support
for a new input format.

## Input
- A file path to a raw input document (`data/raw/corpus/`, `data/fixtures/`, or absolute path).
- The `InputKind` hint (optional — infer from file extension if absent).

## Output
- A `RawContent` object (defined in `ea_mbse_pipeline.ingest.models`) containing:
  - `source`: original file path
  - `kind`: detected `InputKind`
  - `text`: extracted text (empty string if not applicable)
  - `image_paths`: list of extracted image paths (empty if not applicable)
  - `metadata`: arbitrary key-value dict for format-specific attributes

## Behaviour
1. Read `src/ea_mbse_pipeline/ingest/protocols.py` before implementing.
2. Implement `supports(source: Path) → bool` based on file extension and/or MIME type.
3. Implement `ingest(source: Path) → RawContent` using the appropriate library:
   - PDF: `pypdf`
   - Image/screenshot: `pillow`
   - Plain text: stdlib `pathlib`
4. Never store extracted text in memory beyond what is needed for the `RawContent`.
5. Add a fixture in `data/fixtures/<format>.sample.<ext>` and a unit test in
   `tests/unit/test_ingest_<format>.py`.

## Constraints
- Images and screenshots: populate `image_paths`, leave `text` empty; never OCR in this stage.
- Do not perform semantic extraction in this stage — raw extraction only.
- Screenshots must NOT be committed to `data/raw/screenshots/` (gitignored).
- Raise `PipelineError(ErrorCode.INGEST_UNSUPPORTED_FORMAT)` for unknown file types.
- Raise `PipelineError(ErrorCode.INGEST_READ_ERROR)` for I/O failures.
- No `print()` — use `logging.getLogger(__name__)`.

## Quality gates
- `pytest -m unit tests/unit/test_ingest_*.py` passes with no warnings.
- `mypy --strict src/ea_mbse_pipeline/ingest/` passes.
- `ruff check src/ea_mbse_pipeline/ingest/` reports zero issues.
- Every supported format has at least one fixture + unit test.
