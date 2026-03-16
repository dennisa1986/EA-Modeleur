"""Protocols and ABCs for the ingestion stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from ea_mbse_pipeline.ingest.models import RawContent


@runtime_checkable
class IngestorProtocol(Protocol):
    """Structural interface for any ingestor."""

    def ingest(self, source: Path) -> RawContent: ...
    def supports(self, source: Path) -> bool: ...


class BaseIngestor(ABC):
    """Inheritance-based base for ingestor implementations."""

    @abstractmethod
    def ingest(self, source: Path) -> RawContent:
        """Read *source* and return normalised RawContent."""

    @abstractmethod
    def supports(self, source: Path) -> bool:
        """Return True if this ingestor handles the given file type."""
