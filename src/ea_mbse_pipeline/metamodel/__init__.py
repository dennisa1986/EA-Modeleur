"""Stage 2 — Metamodel Compiler.

Reads an XMI metamodel file (EA 17.1 / UML 2.4 profile) and compiles it into
a machine-enforceable RuleSet consumed by the Validation stage.

The metamodel XMI and its written description are normative.

Sprint 3 exports::

    from ea_mbse_pipeline.metamodel import MetamodelCompiler, RuleSet, RuleKind, RuleScope
"""

from ea_mbse_pipeline.metamodel.compiler import MetamodelCompiler
from ea_mbse_pipeline.metamodel.models import MetamodelRule, RuleKind, RuleScope, RuleSet
from ea_mbse_pipeline.metamodel.rule_registry import RuleRegistry

__all__ = [
    "MetamodelCompiler",
    "MetamodelRule",
    "RuleKind",
    "RuleRegistry",
    "RuleScope",
    "RuleSet",
]
