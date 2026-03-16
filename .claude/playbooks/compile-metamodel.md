# Playbook: compile-metamodel

## Purpose
Compile an XMI metamodel file into a `RuleSet` JSON that the `Validator` can
use to check `CanonicalModel` instances.

## Input
- An XMI metamodel file (typically in `data/raw/metamodel/` or `metamodels/`).
- Optional output path for the resulting `RuleSet` JSON.

## Steps
1. Place the XMI file in `data/raw/metamodel/<name>.xmi` if not already there.
2. Invoke the compiler:
   ```
   /compile-metamodel data/raw/metamodel/<name>.xmi [--output data/processed/ruleset.json]
   ```
   Or in Python:
   ```python
   from ea_mbse_pipeline.metamodel.protocols import BaseMetamodelCompiler
   ruleset = compiler.compile(Path("data/raw/metamodel/<name>.xmi"))
   ```
3. Review the printed `RuleSet` summary:
   - Total rule count
   - Rules with severity `"error"` vs `"warning"`
   - Any rules missing `source_xmi_ref`
4. If rules are missing or incorrect, consult the `metamodel-guardian` agent.
5. Optionally save to `data/processed/ruleset.json` for inspection.

## Output
- A `RuleSet` JSON with `source_xmi`, `ea_version`, and a non-empty `rules` list.
- Each `MetamodelRule` has `id`, `description`, `constraint`, `severity`, `source_xmi_ref`.

## Quality gates
- Zero rules with empty `source_xmi_ref`.
- `RuleSet` round-trips through `json.loads(ruleset.model_dump_json())` without data loss.
- At least one rule with severity `"error"` (trivial metamodels still have structural rules).
