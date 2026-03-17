"""Protocols and ABCs for the EA Test stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from ea_mbse_pipeline.ea_test.models import EATestReport
from ea_mbse_pipeline.serialization.models import SerializedArtefact


@runtime_checkable
class EATesterProtocol(Protocol):
    def test(
        self, artefact: SerializedArtefact, golden_path: Path | None = None
    ) -> EATestReport: ...


class BaseEATester(ABC):
    @abstractmethod
    def test(self, artefact: SerializedArtefact, golden_path: Path | None = None) -> EATestReport:
        """Validate *artefact* for EA import readiness.

        If *golden_path* is provided, perform a byte-exact comparison and record
        the result in EATestReport.golden_match.
        """
