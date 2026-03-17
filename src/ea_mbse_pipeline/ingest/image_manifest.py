"""Build image asset manifests from screenshot directories.

Discovers image files, reads basic metadata (dimensions, format) via Pillow
when available, and returns a list of ImageAsset records.

Screenshots are *supporting* input only (see data-governance.md).  This module
intentionally does NOT extract text from images — that is out of scope for the
ingest stage and would require OCR.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ea_mbse_pipeline.ingest.file_discovery import discover_screenshot_files
from ea_mbse_pipeline.ingest.models import ImageAsset
from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)

try:
    from PIL import Image as _PilImage  # type: ignore[import-untyped]
    _PIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PIL_AVAILABLE = False


def build_image_manifest(
    screenshots_dir: Path, *, recursive: bool = True
) -> list[ImageAsset]:
    """Discover all images in *screenshots_dir* and return an ImageAsset list.

    Uses Pillow to read image dimensions and format when available.
    Falls back to dimension-less records if Pillow is not installed or a file
    cannot be read.

    Args:
        screenshots_dir: Directory containing screenshot/image files.
        recursive:       If ``True`` (default), subdirectories are scanned
                         recursively.

    Returns:
        List of ImageAsset instances, one per discovered image file.
    """
    image_paths = discover_screenshot_files(screenshots_dir, recursive=recursive)
    assets: list[ImageAsset] = []
    for path in image_paths:
        asset = _make_asset(path)
        assets.append(asset)
        logger.debug(
            "Image asset: %s  %sx%s  %s",
            path.name,
            asset.width_px or "?",
            asset.height_px or "?",
            asset.format or "unknown",
        )
    logger.info(
        "Image manifest: %d asset(s) from %s",
        len(assets),
        screenshots_dir,
    )
    return assets


def _make_asset(path: Path) -> ImageAsset:
    """Read one image file and return an ImageAsset."""
    width: int | None = None
    height: int | None = None
    fmt: str | None = None

    if _PIL_AVAILABLE:
        try:
            with _PilImage.open(path) as img:
                width, height = img.size
                fmt = img.format
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Cannot read image metadata for '%s': %s",
                path.name, exc,
            )

    return ImageAsset(
        asset_id=str(uuid4()),
        file_path=str(path),
        width_px=width,
        height_px=height,
        format=fmt,
    )
