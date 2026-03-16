"""Golden tests — byte-exact comparison of serializer output against data/golden/.

Naming convention for golden files:
  data/golden/<scenario>.input.json    — canonical model input
  data/golden/<scenario>.golden.xmi   — expected serialized XMI output

To add a new golden scenario:
  1. Place the canonical model JSON in data/golden/<scenario>.input.json
  2. Generate the expected XMI and save as data/golden/<scenario>.golden.xmi
  3. The test is picked up automatically via parametrize.
"""

from __future__ import annotations

from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent.parent.parent / "data" / "golden"


def _golden_scenarios() -> list[str]:
    return [p.stem.replace(".golden", "") for p in GOLDEN_DIR.glob("*.golden.xmi")]


@pytest.mark.golden
@pytest.mark.parametrize("scenario", _golden_scenarios())
def test_serializer_matches_golden(scenario: str) -> None:
    """Serializer output for *scenario* must match the golden XMI."""
    pytest.skip("Awaiting serializer implementation — Sprint 2")
