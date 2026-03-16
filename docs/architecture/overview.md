# Architecture Overview

See `README.md` at the repository root for the pipeline diagram and stage summary.

This directory contains deeper architecture documentation:
- `overview.md` — this file
- *(add ADR references, component diagrams, sequence diagrams as they are produced)*

## Key decisions

| Decision | Location |
|---|---|
| Mandatory canonical model intermediate | `docs/decisions/` (ADR to be written) |
| Provenance on every element | `CLAUDE.md` + `shared/provenance.py` |
| No silent degradation in serializers | `CLAUDE.md` + `serialization/__init__.py` |
| JSON Schema as authoritative contract | `schemas/canonical_model.schema.json` |
