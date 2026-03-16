---
name: validate-canonical
description: Validate a CanonicalModel JSON file against the JSON Schema contract and optionally against a compiled RuleSet, then produce a structured ValidationReport.
---

# Skill: validate-canonical

Validate a `CanonicalModel` JSON and report errors and warnings.

## When to invoke

Use `/validate-canonical <path>` after generating a canonical model, or to re-check a
model before serialization.

```
/validate-canonical data/processed/<name>.canonical.json [--metamodel data/raw/metamodel/<name>.xmi]
```

## Steps

1. **Load and parse the JSON file** at the given path.

2. **Run structural validation** against the JSON Schema:
   ```python
   import json
   import jsonschema
   from pathlib import Path

   schema = json.loads(Path("schemas/canonical_model.schema.json").read_text())
   instance = json.loads(Path("<canonical-path>").read_text())
   jsonschema.validate(instance, schema)  # raises jsonschema.ValidationError on failure
   ```

3. **Run metamodel rule validation** (if `--metamodel` is provided):
   ```python
   from ea_mbse_pipeline.validation import build_validator
   from ea_mbse_pipeline.metamodel import build_compiler

   compiler = build_compiler()
   rule_set = compiler.compile(Path("<xmi-path>"))
   validator = build_validator()
   report = validator.validate(canonical_model, rule_set)
   ```

4. **Print the ValidationReport summary**:
   - `report.passed` (bool)
   - Error count and warning count
   - For each finding: `element_id`, `rule_id`, `severity`, `message`

5. **If errors exist**, trace back to the CanonicalBuilder or Ingest stage.
   Fix there and re-run; do not proceed to serialization with a failing model.

## Quality gates

- `ValidationReport.passed == True` (zero `"error"`-severity findings).
- JSON Schema validation passes independently of the metamodel rule check.
- All element IDs in findings resolve to elements in the model.

## Reference

Full workflow context: `.claude/playbooks/validate-canonical.md`
