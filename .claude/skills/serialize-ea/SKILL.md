---
name: serialize-ea
description: Serialize a validated CanonicalModel into a SerializedArtefact (EA XMI 2.1 or CSV) ready for import into Enterprise Architect 17.1.
---

# Skill: serialize-ea

Serialize a `CanonicalModel` to a `SerializedArtefact` and verify output integrity.

## When to invoke

Use `/serialize-ea` only after validation has passed (`ValidationReport.passed == True`).
Never serialize an invalid model.

```
/serialize-ea data/processed/<name>.canonical.json [--format xmi|csv]
```

Default format is `xmi`.

## Steps

1. **Confirm the canonical model has passed validation**:
   ```bash
   /validate-canonical data/processed/<name>.canonical.json
   ```
   Proceed only if `passed == True`.

2. **Run the serializer**:
   ```bash
   ea-serialize data/processed/<name>.canonical.json --format xmi
   ```
   Or via Python:
   ```python
   from ea_mbse_pipeline.serialization import build_serializer
   from ea_mbse_pipeline.serialization.models import SerializationFormat

   serializer = build_serializer(SerializationFormat.XMI)
   artefact = serializer.serialize(canonical_model)
   ```

3. **Inspect the SerializedArtefact**:
   - `artefact.element_count` equals `len(canonical_model.elements)`.
   - `artefact.filename` ends in `.xmi` (or `.csv` for CSV format).
   - `artefact.content` is non-empty bytes.

4. **For XMI output — verify well-formedness**:
   ```python
   from lxml import etree
   etree.fromstring(artefact.content)  # raises on malformed XML
   ```

5. **Verify EA-specific structure** in the XMI:
   - Root package is named `EA_Model`.
   - All element GUIDs match `{[0-9A-F-]{36}}` (curly-brace-wrapped UUID).
   - Stereotypes are in `<xmi:Extension extender="Enterprise Architect">` blocks.

6. **Save to `outputs/`**:
   ```python
   from pathlib import Path
   Path(f"outputs/{artefact.filename}").write_bytes(artefact.content)
   ```

## Quality gates

- No `PipelineError` raised (especially not `SERIAL_UNMAPPABLE_ELEMENT`).
- `artefact.element_count == len(canonical_model.elements)`.
- XMI parses without error in `lxml`.
- Root package named `EA_Model`.
- All GUIDs match `\{[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\}`.

## Reference

Full workflow context: `.claude/playbooks/serialize-ea.md`
EA XMI conventions: `.claude/rules/ea-xmi-conventions.md`
