# Skill: validate-canonical

## Purpose
Validate a `CanonicalModel` JSON file against the JSON Schema and the compiled
`RuleSet`, then print a human-readable report.

## Usage
```
/validate-canonical <path-to-canonical-model.json> [--metamodel <path-to.xmi>]
```

## Steps
1. Load and parse the JSON file.
2. Validate against `schemas/canonical_model.schema.json`.
3. If `--metamodel` is provided, compile it to a `RuleSet` and run the `Validator`.
4. Print a summary: counts of errors and warnings, with element IDs and rule IDs.
