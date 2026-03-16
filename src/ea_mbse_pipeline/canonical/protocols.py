"""Protocols and ABCs for the canonical model builder stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from ea_mbse_pipeline.canonical.models import CanonicalModel


@runtime_checkable
class CanonicalBuilderProtocol(Protocol):
    def build(self, raw_content: Any) -> CanonicalModel: ...


class BaseCanonicalBuilder(ABC):
    @abstractmethod
    def build(self, raw_content: Any) -> CanonicalModel:
        """Transform ingested RawContent into a CanonicalModel."""
