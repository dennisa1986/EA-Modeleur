"""Shared type aliases used across pipeline stages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# A raw, unvalidated dict — used only at system boundaries (file I/O, external APIs).
RawDict = dict[str, Any]

# Filesystem paths.  Always use Path internally; str only at CLI boundaries.
FilePath = Path
