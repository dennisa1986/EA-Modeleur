"""Structural protocols and ABCs for the metamodel compiler stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from ea_pipeline.metamodel.models import RuleSet


@runtime_checkable
class MetamodelCompilerProtocol(Protocol):
    """Structural interface for XMI → RuleSet compilation."""

    def compile(self, xmi_path: Path) -> RuleSet:
        """Parse *xmi_path* and return a compiled RuleSet."""
        ...


class BaseMetamodelCompiler(ABC):
    """Inheritance-based base for metamodel compiler implementations."""

    @abstractmethod
    def compile(self, xmi_path: Path) -> RuleSet: ...
