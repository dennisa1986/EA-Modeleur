# Agent: import-validator

## Purpose
Implement and maintain the `EA Checks` stage that validates a `SerializedArtefact`
for EA 17.1 import correctness and runs regression checks against golden references.

## Trigger
Use when working on `src/ea_mbse_pipeline/ea_test/` or when an XMI fails to import
into EA or produces unexpected output after import.

## Input
- A `SerializedArtefact` from the Serializer stage.
- An optional `golden_path` (absolute path to a `*.golden.xmi` file in `data/golden/`).

## Output
- An `EATestReport` (defined in `ea_mbse_pipeline.ea_test.models`) containing:
  - `importable`: `True` if the artefact passes all structural checks
  - `golden_match`: `True` / `False` / `None` (None if no golden provided)
  - `issues`: list of `EATestIssue` (xpath, message, severity)

## Behaviour
1. Parse the `SerializedArtefact.content` bytes with `lxml`.
2. Validate EA-specific structural requirements (GUID format, namespace declarations,
   root package name, `xmi:version`).
3. If `golden_path` is provided, compare byte-for-byte against the golden file.
4. Report every deviation as an `EATestIssue` with its XPath location.
5. Only set `importable = True` when zero `"error"`-severity issues remain.

## Constraints
- Do not import or call the `Serializer` from this stage.
- Do not regenerate golden files automatically — golden acceptance requires human review.
- Do not suppress issues by adjusting thresholds — fix the upstream stage instead.
- Raise `PipelineError(ErrorCode.EATEST_PARSE_ERROR)` if the artefact bytes cannot be parsed.
- Raise `PipelineError(ErrorCode.EATEST_GOLDEN_MISMATCH)` only as an error code in
  `EATestIssue`, not as an exception that halts the pipeline (the report carries the result).

## Quality gates
- `EATestReport.importable` is `False` whenever any `"error"`-severity issue exists.
- `EATestIssue.xpath` values are non-empty and valid XPath expressions.
- `pytest -m unit tests/unit/test_ea_test_*.py` passes.
- `mypy --strict src/ea_mbse_pipeline/ea_test/` passes.
