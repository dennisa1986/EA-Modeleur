"""Protocols and ABCs for the validation stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ea_mbse_pipeline.canonical.models import CanonicalModel
from ea_mbse_pipeline.metamodel.models import RuleSet
from ea_mbse_pipeline.validation.models import ValidationReport


@runtime_checkable
class ValidatorProtocol(Protocol):
    def validate(self, model: CanonicalModel, rules: RuleSet) -> ValidationReport: ...


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, model: CanonicalModel, rules: RuleSet) -> ValidationReport:
        """Evaluate all rules against *model* and return a ValidationReport."""
