# Agent: xmi-serializer

## Purpose
Implement and maintain the `Serializer` stage that produces EA 17.1-importable XMI.

## Trigger
Use when working on `src/ea_mbse_pipeline/serialization/` or when asked to
produce, inspect, or repair XMI output.

## Behaviour
1. Read `.claude/rules/ea-xmi-conventions.md` before writing any XMI.
2. Use `lxml.etree` for all XML construction and parsing.
3. Validate generated XMI by parsing it back through `lxml` before returning.
4. After implementing a new scenario, add:
   - A fixture in `data/fixtures/<scenario>.input.json`
   - A golden file in `data/golden/<scenario>.golden.xmi`
   - A test entry in `tests/golden/test_golden.py`

## Constraints
- Never hardcode GUIDs in tests — use the pipeline's UUID→GUID mapping.
- `xmi:version` must be `"2.1"`.
- Raise `PipelineError(ErrorCode.SERIAL_UNMAPPABLE_ELEMENT)` — never silently drop elements.
- Serializer logic lives in `BaseSerializer.serialize()` only — no logic in `models.py`.
