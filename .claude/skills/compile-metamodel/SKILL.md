---
name: compile-metamodel
description: Compile an XMI metamodel file from data/raw/metamodel/ into a RuleSet JSON that the Validator can use to check CanonicalModel instances.
---

# Skill: compile-metamodel

Compile a normative XMI metamodel into a `RuleSet` and verify the output is valid.

## When to invoke

Use `/compile-metamodel` when you need a `RuleSet` for validation, or after a metamodel
XMI file has changed.

```
/compile-metamodel data/raw/metamodel/<name>.xmi [--output data/processed/ruleset.json]
```

## Steps

1. **Confirm the XMI file exists** at `data/raw/metamodel/<name>.xmi`.

2. **Run the compiler**:
   ```bash
   # CLI (when implemented)
   ea-mbse-pipeline compile-metamodel data/raw/metamodel/<name>.xmi \
       --output data/processed/ruleset.json
   ```
   Or via Python:
   ```python
   from pathlib import Path
   from ea_mbse_pipeline.metamodel import build_compiler

   compiler = build_compiler()
   ruleset = compiler.compile(Path("data/raw/metamodel/<name>.xmi"))
   print(f"Rules: {len(ruleset.rules)}, source: {ruleset.source_xmi}")
   ```

3. **Review the RuleSet summary**:
   - Total rule count (must be > 0).
   - Rules with `severity == "error"` — at least one must exist.
   - Inspect any rules missing `source_xmi_ref` — these indicate incomplete parsing.

4. **Optionally save** to `data/processed/ruleset.json`:
   ```python
   import json
   Path("data/processed/ruleset.json").write_text(ruleset.model_dump_json(indent=2))
   ```

5. **If rules appear incorrect or missing**, delegate to the `metamodel-guardian` agent
   (`.claude/agents/metamodel-guardian.md`).

## Quality gates

- Zero rules with empty `source_xmi_ref`.
- At least one rule with `severity == "error"`.
- `RuleSet` round-trips through `json.loads(ruleset.model_dump_json())` without data loss.
- `RuleSet.ea_version` is set and non-empty.

## Reference

Full workflow context: `.claude/playbooks/compile-metamodel.md`
