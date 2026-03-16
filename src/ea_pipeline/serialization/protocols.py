"""Structural protocols and ABCs for the serialization stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ea_pipeline.canonical.models import CanonicalModel
from ea_pipeline.serialization.models import SerializedArtefact


@runtime_checkable
class SerializerProtocol(Protocol):
    def serialize(self, model: CanonicalModel) -> SerializedArtefact: ...


class BaseSerializer(ABC):
    @abstractmethod
    def serialize(self, model: CanonicalModel) -> SerializedArtefact: ...
