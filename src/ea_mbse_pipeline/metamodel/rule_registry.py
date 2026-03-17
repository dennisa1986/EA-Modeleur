"""In-memory constraint registry for compiled metamodel rules (Sprint 3).

``RuleRegistry`` is the runtime indexed form of a ``RuleSet``.  It supports
fast lookup by rule ID, kind, and scope.  Use ``to_rule_set()`` to obtain the
serialisable form and ``from_rule_set()`` to rebuild a registry from a
previously compiled JSON.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from ea_mbse_pipeline.metamodel.models import MetamodelRule, RuleKind, RuleScope, RuleSet

logger = logging.getLogger(__name__)


class RuleRegistry:
    """In-memory index of compiled ``MetamodelRule`` objects.

    Rules are indexed by:
    - ID (unique key)
    - Kind (``RuleKind``)
    - Scope (``RuleScope``)

    Adding a rule with a duplicate ID overwrites the existing entry and
    logs a warning.
    """

    def __init__(self) -> None:
        self._rules: dict[str, MetamodelRule] = {}
        self._by_kind: dict[RuleKind, list[MetamodelRule]] = defaultdict(list)
        self._by_scope: dict[RuleScope, list[MetamodelRule]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, rule: MetamodelRule) -> None:
        """Add *rule* to the registry.  Overwrites if the ID already exists."""
        if rule.id in self._rules:
            logger.warning("Overwriting rule %s in registry", rule.id)
            # Remove old entry from kind/scope indexes
            old = self._rules[rule.id]
            self._by_kind[old.kind] = [r for r in self._by_kind[old.kind] if r.id != rule.id]
            self._by_scope[old.scope] = [r for r in self._by_scope[old.scope] if r.id != rule.id]
        self._rules[rule.id] = rule
        self._by_kind[rule.kind].append(rule)
        self._by_scope[rule.scope].append(rule)

    def add_all(self, rules: list[MetamodelRule]) -> None:
        for rule in rules:
            self.add(rule)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, rule_id: str) -> MetamodelRule | None:
        return self._rules.get(rule_id)

    def by_kind(self, kind: RuleKind) -> list[MetamodelRule]:
        return list(self._by_kind.get(kind, []))

    def by_scope(self, scope: RuleScope) -> list[MetamodelRule]:
        return list(self._by_scope.get(scope, []))

    def all_rules(self) -> list[MetamodelRule]:
        return list(self._rules.values())

    def error_rules(self) -> list[MetamodelRule]:
        return [r for r in self._rules.values() if r.severity == "error"]

    def warning_rules(self) -> list[MetamodelRule]:
        return [r for r in self._rules.values() if r.severity == "warning"]

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: object) -> bool:
        return rule_id in self._rules

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_rule_set(self, source_xmi: str, ea_version: str) -> RuleSet:
        """Export registry contents as a serialisable ``RuleSet``."""
        return RuleSet(
            source_xmi=source_xmi,
            ea_version=ea_version,
            rules=self.all_rules(),
        )

    @classmethod
    def from_rule_set(cls, rule_set: RuleSet) -> "RuleRegistry":
        """Rebuild a ``RuleRegistry`` from a previously compiled ``RuleSet``."""
        registry = cls()
        registry.add_all(rule_set.rules)
        return registry
