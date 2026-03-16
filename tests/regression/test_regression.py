"""Regression tests that compare pipeline output against golden XMI files.

Golden files live in tests/regression/fixtures/.
Naming convention:
  <scenario_name>.input.json   — canonical model input
  <scenario_name>.golden.xmi  — expected serialized output
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _regression_cases() -> list[str]:
    """Discover all *.golden.xmi files and return their scenario names."""
    return [p.stem.replace(".golden", "") for p in FIXTURES_DIR.glob("*.golden.xmi")]


@pytest.mark.regression
@pytest.mark.parametrize("scenario", _regression_cases())
def test_serialization_matches_golden(scenario: str) -> None:
    """Serializer output for *scenario* must match the golden XMI byte-for-byte."""
    pytest.skip("Awaiting serializer implementation.")
