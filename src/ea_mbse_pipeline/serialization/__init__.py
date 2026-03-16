"""Stage 5 — Serialization.

Transforms a validated CanonicalModel into EA-importable artefacts:
  - XMI 2.1  (primary — full model import via EA File → Import/Export → Import XMI)
  - CSV       (secondary — bulk element creation via EA's spreadsheet import)

No silent degradation: if a canonical element cannot be serialised, raise
SerializationError(ErrorCode.SERIAL_UNMAPPABLE_ELEMENT).
"""
