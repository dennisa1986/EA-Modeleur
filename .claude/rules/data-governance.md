# Data Governance

## Data tiers

| Directory | Tier | Committed? | Purpose |
|---|---|---|---|
| `data/raw/metamodel/` | Raw — normative | Yes | XMI metamodel files. These are the single source of truth. |
| `data/raw/corpus/` | Raw — informative | Yes (if small) | PDF / text corpus documents. |
| `data/raw/screenshots/` | Raw — supporting | No (use .gitignore) | Screenshots. Never sole source for canonical elements. |
| `data/processed/` | Derived | No | Intermediate artefacts produced by pipeline runs. |
| `data/fixtures/` | Test fixtures | Yes | Minimal input files used by unit and integration tests. |
| `data/golden/` | Golden artefacts | Yes | Reference XMI/CSV outputs. Add via the ea-test stage. |
| `outputs/` | Pipeline output | No | Final artefacts from production runs. |

## Provenance requirement
Every canonical model element must carry a `Provenance` object with at least
one `SourceRef` pointing to an item in `data/raw/` or `data/fixtures/`.

Elements where `derivation_method` is `'ocr'` or `'image-extraction'` must
have a second `SourceRef` pointing to a corroborating text or metamodel source.

## Golden file lifecycle
1. A golden file is created when a serializer output is manually reviewed and
   accepted as correct.
2. Golden files are committed under `data/golden/`.
3. Any change to the serializer that alters golden output requires explicit
   review and re-acceptance before committing the updated golden file.
4. Do not auto-regenerate golden files in CI without a human review step.

## Screenshots
- Store in `data/raw/screenshots/` — do NOT commit large images to git.
- Add `data/raw/screenshots/` to `.gitignore` for the project.
- Reference screenshots in `SourceRef.file_path` using repo-relative paths.
