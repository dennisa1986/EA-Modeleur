# Playbook: run-import-validation

## Purpose
Run structural and regression checks on a `SerializedArtefact` to confirm it
is importable into Enterprise Architect 17.1 and matches the golden reference.

## Input
- A `SerializedArtefact` (output from the Serializer stage).
- Optional: path to a golden reference file in `data/golden/<scenario>.golden.xmi`.

## Steps
1. Run the EA Checks stage:
   ```python
   report = ea_tester.test(artefact, golden_path=Path("data/golden/<scenario>.golden.xmi"))
   ```
2. Review `EATestReport`:
   - `importable`: must be `True` to proceed.
   - `golden_match`: `True` confirms no regression; `False` requires review.
   - `issues`: list of `EATestIssue` — fix all `"error"`-severity items.
3. For each `EATestIssue`:
   - Use `issue.xpath` to locate the element in the XMI.
   - Trace back to the serializer or canonical model to find the root cause.
   - Fix in the upstream stage; re-run the full pipeline.
4. If `golden_match == False` and the change is intentional:
   - Review the diff manually.
   - Accept the new output by replacing `data/golden/<scenario>.golden.xmi`.
   - Commit the updated golden file with an explicit review note.

## Output
- An `EATestReport` with `importable`, `golden_match`, and `issues`.
- Zero `"error"`-severity issues for the artefact to be considered production-ready.

## Quality gates
- `EATestReport.importable == True`.
- Zero `"error"`-severity `EATestIssue` entries.
- `golden_match == True` (or golden file explicitly updated after human review).
- Never auto-accept golden changes in CI without a human approval step.
