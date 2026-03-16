"""Structural protocols and ABCs for the canonical model builder stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from ea_pipeline.canonical.models import CanonicalModel


@runtime_checkable
class CanonicalModelBuilderProtocol(Protocol):
    """Builds a CanonicalModel from normalised raw content."""

    def build(self, raw_content: dict[str, Any]) -> CanonicalModel:
        """Transform *raw_content* (Stage 1 output) into a CanonicalModel."""
        ...


class BaseCanonicalModelBuilder(ABC):
    """Inheritance-based base for canonical model builder implementations."""

    @abstractmethod
    def build(self, raw_content: dict[str, Any]) -> CanonicalModel: ...
