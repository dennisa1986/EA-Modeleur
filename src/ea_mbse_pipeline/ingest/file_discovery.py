"""File discovery utilities for all ingest source directories.

Responsible for:
  - Scanning corpus directory for PDF and text files
  - Scanning metamodel directory for XMI/XML files
  - Scanning screenshots directory for image files
  - Ensuring required output directories exist

Does NOT perform any content extraction — only path enumeration.

Recursive discovery
-------------------
All three ``discover_*`` functions accept a ``recursive`` keyword argument
(default ``True``).  When ``recursive=True`` the scan uses ``Path.rglob``
and descends into subdirectories; when ``False`` only the top-level
directory is examined (``Path.iterdir``).  Results are always sorted by
full path so the order is deterministic regardless of directory depth.
"""

from __future__ import annotations

from pathlib import Path

from ea_mbse_pipeline.shared.logging import get_logger

logger = get_logger(__name__)

# Supported file extensions per source type
_CORPUS_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".txt",
        ".md",
        ".rst",
        ".text",
    }
)
_METAMODEL_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".xmi",
        ".xml",
    }
)
_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
    }
)


def _iter_files(directory: Path, *, recursive: bool) -> list[Path]:
    """Return all files under *directory*, optionally recursing into subdirs.

    Results are sorted by full path for deterministic ordering.
    Symlinks to directories are not followed.
    """
    candidates = directory.rglob("*") if recursive else directory.iterdir()
    return sorted(p for p in candidates if p.is_file())


def discover_corpus_files(corpus_dir: Path, *, recursive: bool = True) -> list[Path]:
    """Return all supported corpus files in *corpus_dir*, sorted by path.

    Supported extensions: .pdf, .txt, .md, .rst, .text

    Args:
        corpus_dir: Directory to search.
        recursive:  If ``True`` (default), subdirectories are searched
                    recursively.  If ``False``, only the top-level directory
                    is scanned.

    Returns:
        Sorted list of matching paths.  Empty list (with a warning) if the
        directory does not exist.
    """
    if not corpus_dir.exists():
        logger.warning("Corpus directory does not exist: %s", corpus_dir)
        return []
    files = [
        p
        for p in _iter_files(corpus_dir, recursive=recursive)
        if p.suffix.lower() in _CORPUS_EXTENSIONS
    ]
    logger.info(
        "Discovered %d corpus file(s) in %s (recursive=%s)",
        len(files),
        corpus_dir,
        recursive,
    )
    return files


def discover_metamodel_files(metamodel_dir: Path, *, recursive: bool = True) -> list[Path]:
    """Return all XMI/XML files in *metamodel_dir*, sorted by path.

    These files are not ingested as corpus — they are listed in the manifest
    for the MetamodelCompiler stage.

    Args:
        metamodel_dir: Directory to search.
        recursive:     If ``True`` (default), subdirectories are searched
                       recursively.

    Returns:
        Sorted list of matching paths.  Empty list (with a warning) if the
        directory does not exist.
    """
    if not metamodel_dir.exists():
        logger.warning("Metamodel directory does not exist: %s", metamodel_dir)
        return []
    files = [
        p
        for p in _iter_files(metamodel_dir, recursive=recursive)
        if p.suffix.lower() in _METAMODEL_EXTENSIONS
    ]
    logger.info(
        "Discovered %d metamodel file(s) in %s (recursive=%s)",
        len(files),
        metamodel_dir,
        recursive,
    )
    return files


def discover_screenshot_files(screenshots_dir: Path, *, recursive: bool = True) -> list[Path]:
    """Return all image files in *screenshots_dir*, sorted by path.

    Args:
        screenshots_dir: Directory to search.
        recursive:       If ``True`` (default), subdirectories are searched
                         recursively.

    Returns:
        Sorted list of matching paths.  Empty list (without warning) if the
        directory does not exist — screenshots are optional input.
    """
    if not screenshots_dir.exists():
        logger.debug("Screenshots directory does not exist: %s", screenshots_dir)
        return []
    files = [
        p
        for p in _iter_files(screenshots_dir, recursive=recursive)
        if p.suffix.lower() in _IMAGE_EXTENSIONS
    ]
    logger.info(
        "Discovered %d screenshot(s) in %s (recursive=%s)",
        len(files),
        screenshots_dir,
        recursive,
    )
    return files


def ensure_directory(path: Path) -> Path:
    """Create *path* and all parents if they do not already exist.

    Returns *path* for chaining.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
