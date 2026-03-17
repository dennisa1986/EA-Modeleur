"""Unit tests for file discovery utilities.

All tests are isolated — no network access, no production data directories.
Tests use pytest's tmp_path fixture for all filesystem operations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ea_mbse_pipeline.ingest.file_discovery import (
    discover_corpus_files,
    discover_metamodel_files,
    discover_screenshot_files,
    ensure_directory,
)

# ---------------------------------------------------------------------------
# discover_corpus_files
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiscoverCorpusFiles:
    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        assert discover_corpus_files(tmp_path) == []

    def test_missing_directory_returns_empty(self, tmp_path: Path) -> None:
        result = discover_corpus_files(tmp_path / "nonexistent")
        assert result == []

    def test_supported_extensions_discovered(self, tmp_path: Path) -> None:
        (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "notes.txt").write_text("hello")
        (tmp_path / "readme.md").write_text("# Title")
        (tmp_path / "spec.rst").write_text("Spec")
        (tmp_path / "data.text").write_text("data")
        result = discover_corpus_files(tmp_path)
        names = {p.name for p in result}
        assert names == {"doc.pdf", "notes.txt", "readme.md", "spec.rst", "data.text"}

    def test_unsupported_extensions_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "binary.bin").write_bytes(b"\x00\x01")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        (tmp_path / "archive.zip").write_bytes(b"PK")
        result = discover_corpus_files(tmp_path)
        assert result == []

    def test_results_sorted_by_path(self, tmp_path: Path) -> None:
        (tmp_path / "c.txt").write_text("c")
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        result = discover_corpus_files(tmp_path)
        assert result == sorted(result)

    # ------------------------------------------------------------------
    # Recursive discovery
    # ------------------------------------------------------------------

    def test_recursive_default_discovers_subdirectory_files(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.txt").write_text("top level")
        (sub / "nested.txt").write_text("nested")
        result = discover_corpus_files(tmp_path)  # recursive=True is default
        names = [p.name for p in result]
        assert "top.txt" in names
        assert "nested.txt" in names

    def test_recursive_true_discovers_deeply_nested_files(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("deep content")
        result = discover_corpus_files(tmp_path, recursive=True)
        assert any(p.name == "deep.txt" for p in result)

    def test_recursive_false_skips_subdirectory_files(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.txt").write_text("top level")
        (sub / "nested.txt").write_text("nested")
        result = discover_corpus_files(tmp_path, recursive=False)
        names = [p.name for p in result]
        assert "top.txt" in names
        assert "nested.txt" not in names

    def test_recursive_results_sorted_across_subdirectories(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "b.txt").write_text("b")
        (sub / "a.txt").write_text("a")
        result = discover_corpus_files(tmp_path, recursive=True)
        assert result == sorted(result)

    def test_directories_not_returned_as_files(self, tmp_path: Path) -> None:
        fake_dir = tmp_path / "corpus.txt"
        fake_dir.mkdir()  # a *directory* with a .txt suffix
        result = discover_corpus_files(tmp_path)
        assert result == []

    def test_multiple_subdirectories_all_scanned(self, tmp_path: Path) -> None:
        for name in ("alpha", "beta", "gamma"):
            sub = tmp_path / name
            sub.mkdir()
            (sub / f"{name}.pdf").write_bytes(b"%PDF-1.4")
        result = discover_corpus_files(tmp_path, recursive=True)
        names = {p.name for p in result}
        assert names == {"alpha.pdf", "beta.pdf", "gamma.pdf"}


# ---------------------------------------------------------------------------
# discover_metamodel_files
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiscoverMetamodelFiles:
    def test_xmi_files_discovered(self, tmp_path: Path) -> None:
        (tmp_path / "model.xmi").write_bytes(b"<xmi/>")
        result = discover_metamodel_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "model.xmi"

    def test_xml_files_discovered(self, tmp_path: Path) -> None:
        (tmp_path / "config.xml").write_bytes(b"<config/>")
        result = discover_metamodel_files(tmp_path)
        assert len(result) == 1

    def test_non_xmi_extensions_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("notes")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        result = discover_metamodel_files(tmp_path)
        assert result == []

    def test_missing_directory_returns_empty(self, tmp_path: Path) -> None:
        result = discover_metamodel_files(tmp_path / "missing")
        assert result == []

    def test_recursive_discovers_nested_xmi(self, tmp_path: Path) -> None:
        sub = tmp_path / "profiles"
        sub.mkdir()
        (sub / "archimate.xmi").write_bytes(b"<xmi/>")
        result = discover_metamodel_files(tmp_path, recursive=True)
        assert any(p.name == "archimate.xmi" for p in result)

    def test_non_recursive_skips_nested_xmi(self, tmp_path: Path) -> None:
        sub = tmp_path / "profiles"
        sub.mkdir()
        (sub / "archimate.xmi").write_bytes(b"<xmi/>")
        result = discover_metamodel_files(tmp_path, recursive=False)
        assert result == []

    def test_results_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "z.xmi").write_bytes(b"<z/>")
        (tmp_path / "a.xmi").write_bytes(b"<a/>")
        result = discover_metamodel_files(tmp_path)
        assert result == sorted(result)


# ---------------------------------------------------------------------------
# discover_screenshot_files
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiscoverScreenshotFiles:
    def test_missing_directory_returns_empty_without_error(self, tmp_path: Path) -> None:
        result = discover_screenshot_files(tmp_path / "nonexistent")
        assert result == []

    def test_image_extensions_discovered(self, tmp_path: Path) -> None:
        (tmp_path / "screen.png").write_bytes(b"\x89PNG")
        (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff")
        (tmp_path / "capture.bmp").write_bytes(b"BM")
        result = discover_screenshot_files(tmp_path)
        names = {p.name for p in result}
        assert names == {"screen.png", "photo.jpg", "capture.bmp"}

    def test_non_image_extensions_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text("not an image")
        result = discover_screenshot_files(tmp_path)
        assert result == []

    def test_recursive_discovers_nested_screenshots(self, tmp_path: Path) -> None:
        sub = tmp_path / "session1"
        sub.mkdir()
        (sub / "capture.png").write_bytes(b"\x89PNG")
        result = discover_screenshot_files(tmp_path, recursive=True)
        assert any(p.name == "capture.png" for p in result)

    def test_non_recursive_skips_nested_screenshots(self, tmp_path: Path) -> None:
        sub = tmp_path / "session1"
        sub.mkdir()
        (sub / "capture.png").write_bytes(b"\x89PNG")
        result = discover_screenshot_files(tmp_path, recursive=False)
        assert result == []

    def test_results_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "b.png").write_bytes(b"\x89PNG")
        (tmp_path / "a.png").write_bytes(b"\x89PNG")
        result = discover_screenshot_files(tmp_path)
        assert result == sorted(result)


# ---------------------------------------------------------------------------
# ensure_directory
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEnsureDirectory:
    def test_creates_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "new_dir"
        assert not target.exists()
        ensure_directory(target)
        assert target.is_dir()

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        ensure_directory(target)
        assert target.is_dir()

    def test_existing_directory_no_error(self, tmp_path: Path) -> None:
        ensure_directory(tmp_path)  # already exists — must not raise
        assert tmp_path.is_dir()

    def test_returns_path_for_chaining(self, tmp_path: Path) -> None:
        target = tmp_path / "out"
        result = ensure_directory(target)
        assert result == target
