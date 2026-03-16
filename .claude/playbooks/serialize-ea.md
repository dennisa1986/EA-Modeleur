# Playbook: serialize-ea

## Purpose
Serialize a validated `CanonicalModel` into a `SerializedArtefact` using the
configured serializer plugin (e.g., EA XMI 2.1 or CSV).

## Input
- A `CanonicalModel` that has passed validation (`ValidationReport.passed == True`).
- The target `SerializationFormat` (default: `XMI`).

## Steps
1. Confirm the `CanonicalModel` has passed validation — do not serialize invalid models.
2. Run the serializer:
   ```python
   artefact = serializer.serialize(canonical_model)
   ```
   Or via CLI:
   ```
   ea-serialize <path-to-canonical.json> [--format xmi|csv]
   ```
3. Inspect the `SerializedArtefact`:
   - `element_count` matches the number of elements in the `CanonicalModel`.
   - `filename` has the correct extension (`.xmi` or `.csv`).
4. For XMI output, re-parse with `lxml` to confirm well-formedness:
   ```python
   from lxml import etree
   etree.fromstring(artefact.content)
   ```
5. Save to `outputs/<run-id>.<ext>` for EA import.

## Output
- A `SerializedArtefact` with `format`, `content` (bytes), `filename`, `element_count`.
- For XMI: a well-formed XMI 2.1 file with EA-style GUIDs and EA root package `EA_Model`.

## Quality gates
- `artefact.element_count` equals `len(canonical_model.elements)`.
- XMI parses without error in `lxml`.
- GUIDs match `{[0-9A-F-]{36}}` format (curly-brace-wrapped UUID).
- Root package is named `EA_Model`.
- No `PipelineError` raised during serialization.
