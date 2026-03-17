"""Protocols and ABCs for the metamodel compiler stage.

Sprint 3: adds XMIParserProtocol and DescriptionParserProtocol so each
sub-component is independently mockable and testable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from ea_mbse_pipeline.metamodel.models import RuleSet

if TYPE_CHECKING:
    from ea_mbse_pipeline.metamodel.description_parser import DescriptionParseResult
    from ea_mbse_pipeline.metamodel.xmi_parser import XMIParseResult


@runtime_checkable
class MetamodelCompilerProtocol(Protocol):
    def compile(self, xmi_path: Path) -> RuleSet: ...


class BaseMetamodelCompiler(ABC):
    @abstractmethod
    def compile(self, xmi_path: Path) -> RuleSet:
        """Parse *xmi_path* and return a compiled RuleSet."""


@runtime_checkable
class XMIParserProtocol(Protocol):
    def parse(self, xmi_path: Path) -> "XMIParseResult": ...


@runtime_checkable
class DescriptionParserProtocol(Protocol):
    def parse(self, description_path: Path) -> "DescriptionParseResult": ...
