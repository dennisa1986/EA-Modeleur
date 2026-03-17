"""Protocols and ABCs for the metamodel compiler stage.

Sprint 3: adds XMIParserProtocol and DescriptionParserProtocol so each
sub-component is independently mockable and testable.

Sprint 3.1: MetamodelCompilerProtocol and BaseMetamodelCompiler are extended
to reflect the full public API: compile(), compile_full(), compile_and_export().
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

    def compile_full(
        self,
        xmi_path: Path,
        description_path: Path | None = None,
    ) -> RuleSet: ...

    def compile_and_export(
        self,
        xmi_path: Path,
        description_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> tuple[RuleSet, Path, Path]: ...


class BaseMetamodelCompiler(ABC):
    @abstractmethod
    def compile(self, xmi_path: Path) -> RuleSet:
        """Parse *xmi_path* and return a compiled RuleSet (XMI only)."""

    @abstractmethod
    def compile_full(
        self,
        xmi_path: Path,
        description_path: Path | None = None,
    ) -> RuleSet:
        """Compile XMI + optional description into a RuleSet."""

    @abstractmethod
    def compile_and_export(
        self,
        xmi_path: Path,
        description_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> tuple[RuleSet, Path, Path]:
        """Compile, then write JSON + Markdown to *output_dir*.

        Returns ``(rule_set, json_path, markdown_path)``.
        """


@runtime_checkable
class XMIParserProtocol(Protocol):
    def parse(self, xmi_path: Path) -> "XMIParseResult": ...


@runtime_checkable
class DescriptionParserProtocol(Protocol):
    def parse(self, description_path: Path) -> "DescriptionParseResult": ...
