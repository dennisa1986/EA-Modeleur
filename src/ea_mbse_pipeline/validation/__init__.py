"""Stage 4 — Validation.

Validates a CanonicalModel against the RuleSet produced by the MetamodelCompiler.
All 'error'-severity findings halt the pipeline.  'warning'-severity findings are
recorded in the ValidationReport and logged, but do not halt.
"""
