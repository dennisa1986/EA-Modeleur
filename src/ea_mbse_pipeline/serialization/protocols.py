"""Protocols and ABCs for the serialization stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ea_mbse_pipeline.canonical.models import CanonicalModel
from ea_mbse_pipeline.serialization.models import SerializedArtefact


@runtime_checkable
class SerializerProtocol(Protocol):
    def serialize(self, model: CanonicalModel) -> SerializedArtefact: ...


class BaseSerializer(ABC):
    @abstractmethod
    def serialize(self, model: CanonicalModel) -> SerializedArtefact:
        """Serialise *model* to an EA-importable artefact.

        Raises SerializationError (SERIAL_UNMAPPABLE_ELEMENT) if any element
        cannot be mapped to a valid XMI construct.  Never returns partial output.
        """
