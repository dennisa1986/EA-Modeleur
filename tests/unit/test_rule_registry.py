"""Unit tests for RuleRegistry.

Pure in-memory tests — no filesystem or network I/O.
"""

from __future__ import annotations

import pytest

from ea_mbse_pipeline.metamodel.models import MetamodelRule, RuleKind, RuleScope, RuleSet
from ea_mbse_pipeline.metamodel.rule_registry import RuleRegistry


def _make_rule(
    rule_id: str,
    kind: RuleKind = RuleKind.GENERAL,
    scope: RuleScope = RuleScope.ELEMENT,
    severity: str = "error",
) -> MetamodelRule:
    return MetamodelRule(
        id=rule_id,
        kind=kind,
        scope=scope,
        description=f"Test rule {rule_id}",
        severity=severity,
    )


@pytest.mark.unit
class TestRuleRegistryBasic:
    def test_empty_registry_has_zero_length(self) -> None:
        registry = RuleRegistry()
        assert len(registry) == 0

    def test_add_and_get(self) -> None:
        registry = RuleRegistry()
        rule = _make_rule("R-001")
        registry.add(rule)
        assert registry.get("R-001") is rule

    def test_contains(self) -> None:
        registry = RuleRegistry()
        registry.add(_make_rule("R-001"))
        assert "R-001" in registry
        assert "R-999" not in registry

    def test_add_all(self) -> None:
        registry = RuleRegistry()
        rules = [_make_rule(f"R-{i:03d}") for i in range(5)]
        registry.add_all(rules)
        assert len(registry) == 5

    def test_all_rules_returns_all(self) -> None:
        registry = RuleRegistry()
        registry.add_all([_make_rule("R-001"), _make_rule("R-002")])
        assert len(registry.all_rules()) == 2

    def test_overwrite_existing_rule(self) -> None:
        registry = RuleRegistry()
        registry.add(_make_rule("R-001", severity="error"))
        registry.add(_make_rule("R-001", severity="warning"))
        assert len(registry) == 1
        assert registry.get("R-001").severity == "warning"  # type: ignore[union-attr]


@pytest.mark.unit
class TestRuleRegistryIndexing:
    def test_by_kind(self) -> None:
        registry = RuleRegistry()
        registry.add(_make_rule("R-001", kind=RuleKind.CONNECTOR))
        registry.add(_make_rule("R-002", kind=RuleKind.CONNECTOR))
        registry.add(_make_rule("R-003", kind=RuleKind.NAMING))
        assert len(registry.by_kind(RuleKind.CONNECTOR)) == 2
        assert len(registry.by_kind(RuleKind.NAMING)) == 1

    def test_by_scope(self) -> None:
        registry = RuleRegistry()
        registry.add(_make_rule("R-001", scope=RuleScope.ELEMENT))
        registry.add(_make_rule("R-002", scope=RuleScope.RELATIONSHIP))
        assert len(registry.by_scope(RuleScope.ELEMENT)) == 1
        assert len(registry.by_scope(RuleScope.RELATIONSHIP)) == 1

    def test_error_rules(self) -> None:
        registry = RuleRegistry()
        registry.add(_make_rule("R-001", severity="error"))
        registry.add(_make_rule("R-002", severity="warning"))
        assert len(registry.error_rules()) == 1
        assert len(registry.warning_rules()) == 1


@pytest.mark.unit
class TestRuleRegistryConversion:
    def test_to_rule_set(self) -> None:
        registry = RuleRegistry()
        registry.add(_make_rule("R-001"))
        rs = registry.to_rule_set(source_xmi="model.xmi", ea_version="17.1")
        assert isinstance(rs, RuleSet)
        assert rs.source_xmi == "model.xmi"
        assert rs.ea_version == "17.1"
        assert len(rs.rules) == 1

    def test_from_rule_set_roundtrip(self) -> None:
        original = RuleRegistry()
        original.add_all([_make_rule("R-001"), _make_rule("R-002")])
        rs = original.to_rule_set(source_xmi="m.xmi", ea_version="17.1")

        restored = RuleRegistry.from_rule_set(rs)
        assert len(restored) == 2
        assert "R-001" in restored
        assert "R-002" in restored

    def test_kind_index_intact_after_roundtrip(self) -> None:
        original = RuleRegistry()
        original.add(_make_rule("R-001", kind=RuleKind.CONNECTOR))
        rs = original.to_rule_set(source_xmi="m.xmi", ea_version="17.1")
        restored = RuleRegistry.from_rule_set(rs)
        assert len(restored.by_kind(RuleKind.CONNECTOR)) == 1
