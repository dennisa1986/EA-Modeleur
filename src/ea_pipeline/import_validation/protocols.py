"""Structural protocols and ABCs for the import validation stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ea_pipeline.import_validation.models import ImportReport
from ea_pipeline.serialization.models import SerializedArtefact


@runtime_checkable
class ImportValidatorProtocol(Protocol):
    def validate_import(self, artefact: SerializedArtefact) -> ImportReport: ...


class BaseImportValidator(ABC):
    @abstractmethod
    def validate_import(self, artefact: SerializedArtefact) -> ImportReport: ...
