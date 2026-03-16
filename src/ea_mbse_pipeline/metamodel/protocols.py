"""Protocols and ABCs for the metamodel compiler stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from ea_mbse_pipeline.metamodel.models import RuleSet


@runtime_checkable
class MetamodelCompilerProtocol(Protocol):
    def compile(self, xmi_path: Path) -> RuleSet: ...


class BaseMetamodelCompiler(ABC):
    @abstractmethod
    def compile(self, xmi_path: Path) -> RuleSet:
        """Parse *xmi_path* and return a compiled RuleSet."""
