"""Structural protocols and ABCs for the ingestion stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IngestorProtocol(Protocol):
    """Structural interface: anything that can ingest a raw input file."""

    def ingest(self, source: Path) -> dict[str, Any]:
        """Read *source* and return a normalised raw-content dict."""
        ...


class BaseIngestor(ABC):
    """Inheritance-based base for ingestor implementations."""

    @abstractmethod
    def ingest(self, source: Path) -> dict[str, Any]:
        """Read *source* and return a normalised raw-content dict."""

    def supports(self, source: Path) -> bool:
        """Return True if this ingestor can handle the given file type."""
        raise NotImplementedError
