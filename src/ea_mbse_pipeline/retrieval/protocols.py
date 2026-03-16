"""Protocols and ABCs for the retrieval stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ea_mbse_pipeline.retrieval.models import RetrievalResult


@runtime_checkable
class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult: ...


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Retrieve the *top_k* most relevant chunks for *query*."""
