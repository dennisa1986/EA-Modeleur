# Agent: ea-serializer

## Purpose
Implement and maintain the `Serializer` stage that converts a validated `CanonicalModel`
into a `SerializedArtefact` suitable for import into Enterprise Architect 17.1.

## Trigger
Use when working on `src/ea_mbse_pipeline/serialization/` or when asked to produce,
inspect, repair, or extend serialized output.

## Input
- A validated `CanonicalModel` (must have passed `ValidationReport.passed == True`).
- The target `SerializationFormat` (e.g., `XMI`, `CSV`).

## Output
- A `SerializedArtefact` (defined in `ea_mbse_pipeline.serialization.models`) containing:
  - `format`: the `SerializationFormat` used
  - `content`: the serialized bytes
  - `filename`: suggested output filename (with extension)
  - `element_count`: number of elements serialized

## Behaviour
1. Read `.claude/rules/ea-xmi-conventions.md` before writing any XMI.
2. Use `lxml.etree` for all XML construction and parsing — never stdlib `xml`.
3. Map every `ModelElement.id` (UUID) to an EA-style GUID `{UUID}` — never hardcode GUIDs.
4. Wrap stereotypes in `<xmi:Extension extender="Enterprise Architect">` blocks.
5. Place diagrams in the `<xmi:Extension>` block, not in the UML namespace.
6. After producing XMI, re-parse it through `lxml` to verify well-formedness.
7. For each new scenario, add:
   - `data/fixtures/<scenario>.input.json` (canonical model input)
   - `data/golden/<scenario>.golden.xmi` (expected XMI output)
   - An entry in `tests/golden/test_golden.py`

## Constraints
- Target format is pluggable (`SerializerProtocol`) — do not hard-wire format logic
  into the orchestrator.
- `xmi:version` must always be `"2.1"`.
- Root package must be named `EA_Model`.
- Raise `PipelineError(ErrorCode.SERIAL_UNMAPPABLE_ELEMENT)` if any element cannot be
  mapped. Never silently drop elements or substitute placeholders.
- Serializer logic lives in `BaseSerializer.serialize()` only — no logic in `models.py`.
- Do not call the `Validator` from within the serializer.

## Quality gates
- All golden tests in `tests/golden/test_golden.py` pass byte-for-byte.
- Generated XMI parses without error in `lxml`.
- `pytest -m golden` passes.
- `mypy --strict src/ea_mbse_pipeline/serialization/` passes.
- `ruff check src/ea_mbse_pipeline/serialization/` reports zero issues.
