# Playbook: validate-canonical

## Purpose
Validate a `CanonicalModel` JSON file against the JSON Schema contract and,
optionally, against a compiled `RuleSet`, then produce a human-readable report.

## Input
- Path to a `CanonicalModel` JSON file.
- Optional: path to an XMI metamodel file (to compile and apply rules).

## Steps
1. Load and parse the JSON file.
2. Validate against `schemas/canonical_model.schema.json` (structural check):
   ```
   /validate-canonical <path-to-canonical-model.json>
   ```
3. If a metamodel path is provided, compile it and run the `Validator`:
   ```
   /validate-canonical <path-to-canonical-model.json> --metamodel <path-to.xmi>
   ```
4. Review the summary output:
   - Total element / relationship / diagram count
   - Error count (must be zero for the model to be considered valid)
   - Warning count (advisory — review before proceeding to serialization)
   - Element IDs and rule IDs for each finding
5. Fix reported errors in the upstream stage (canonical builder or ingestion) before proceeding.

## Output
- A `ValidationReport` with `passed` (bool), `findings` (list), `errors`, `warnings`.
- Console summary: error/warning counts, element IDs, rule IDs.

## Quality gates
- `ValidationReport.passed == True` (zero error-severity findings).
- All element IDs referenced in findings resolve to elements in the model.
- JSON Schema validation passes independently of the metamodel rule check.
