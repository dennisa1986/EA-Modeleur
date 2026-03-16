---
name: run-import-validation
description: Run structural and regression checks on a SerializedArtefact to confirm it is importable into Enterprise Architect 17.1 and matches the golden reference output.
---

# Skill: run-import-validation

Run EA import checks on a `SerializedArtefact` and verify it against the golden reference.

## When to invoke

Use `/run-import-validation` after serialization, as the final pipeline gate before
an artefact is considered production-ready.

```
/run-import-validation outputs/<name>.xmi [--golden data/golden/<scenario>.golden.xmi]
```

## Steps

1. **Run the EA Checks stage**:
   ```python
   from pathlib import Path
   from ea_mbse_pipeline.ea_test import build_ea_tester

   tester = build_ea_tester()
   report = tester.test(
       artefact,
       golden_path=Path("data/golden/<scenario>.golden.xmi"),  # optional
   )
   ```

2. **Check `EATestReport.importable`** — must be `True`.
   If `False`, do not proceed; fix errors before re-running.

3. **Check `EATestReport.golden_match`**:
   - `True` → no regression, artefact is production-ready.
   - `False` → diff the output against the golden file and determine whether the
     change is intentional or a bug.

4. **Fix all `"error"`-severity `EATestIssue` entries**:
   - Use `issue.xpath` to locate the element in the XMI.
   - Trace the root cause to the serializer or canonical model.
   - Fix in the upstream stage, then re-run the full pipeline.

5. **If `golden_match == False` and the change is intentional**:
   - Review the diff manually (human review required).
   - Accept the new output by replacing the golden file:
     ```bash
     cp outputs/<name>.xmi data/golden/<scenario>.golden.xmi
     git add data/golden/<scenario>.golden.xmi
     git commit -m "chore: accept updated golden artefact for <scenario>"
     ```
   - **Never auto-accept golden changes in CI without human approval.**

## Quality gates

- `EATestReport.importable == True`.
- Zero `"error"`-severity `EATestIssue` entries.
- `golden_match == True`, or golden file explicitly updated after human review.
- Golden file changes are committed with a review note in the commit message.

## Reference

Full workflow context: `.claude/playbooks/run-import-validation.md`
Data governance (golden lifecycle): `.claude/rules/data-governance.md`
