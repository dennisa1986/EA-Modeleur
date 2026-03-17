"""Integration tests for the ingest pipeline stage.

These tests touch the filesystem and read real fixture files from data/fixtures/.
They verify end-to-end behaviour of IngestPipeline.run() including file
discovery, extraction, chunking, and JSON/SQLite output.

Marked @pytest.mark.integration — not run in fast unit-only mode.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ea_mbse_pipeline.ingest.models import IngestRunManifest, InputKind
from ea_mbse_pipeline.ingest.pipeline import IngestPipeline, build_ingestor

# Fixture files committed under data/fixtures/
FIXTURES_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"


@pytest.mark.integration
class TestIngestPipelineRun:
    def test_run_produces_manifest(self, tmp_path: Path) -> None:
        """Pipeline run returns a valid IngestRunManifest."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        assert isinstance(manifest, IngestRunManifest)
        assert manifest.run_id
        assert manifest.started_at is not None
        assert manifest.finished_at is not None
        assert manifest.finished_at >= manifest.started_at

    def test_text_fixture_ingested(self, tmp_path: Path) -> None:
        """sample_corpus.txt is discovered, ingested, and produces chunks."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        txt_docs = [d for d in manifest.source_documents if d.file_name == "sample_corpus.txt"]
        assert len(txt_docs) >= 1, "sample_corpus.txt must be ingested"
        doc = txt_docs[0]
        assert doc.source_type == InputKind.TEXT
        assert doc.char_count is not None and doc.char_count > 0
        assert doc.doc_id.startswith("doc-")

    def test_chunks_produced_from_fixture(self, tmp_path: Path) -> None:
        """At least one CorpusChunk is produced from sample_corpus.txt."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        assert manifest.chunk_count >= 1

    def test_chunks_have_provenance(self, tmp_path: Path) -> None:
        """Every chunk has at least one provenance_source."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        for chunk in manifest.chunks:
            assert len(chunk.provenance_sources) >= 1
            assert chunk.provenance_sources[0].file_path

    def test_xmi_fixture_discovered(self, tmp_path: Path) -> None:
        """sample_metamodel.xmi is listed in manifest.xmi_files."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        xmi_names = [Path(p).name for p in manifest.xmi_files]
        assert "sample_metamodel.xmi" in xmi_names

    def test_manifest_json_written(self, tmp_path: Path) -> None:
        """manifest.json is written to the output directory."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        assert manifest.output_json_path
        json_path = Path(manifest.output_json_path)
        assert json_path.exists()
        # File must be valid JSON containing the run_id
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["run_id"] == manifest.run_id

    def test_chunks_json_written(self, tmp_path: Path) -> None:
        """chunks.json is written alongside manifest.json."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        assert manifest.output_json_path
        chunks_path = Path(manifest.output_json_path).parent / "chunks.json"
        assert chunks_path.exists()
        data = json.loads(chunks_path.read_text(encoding="utf-8"))
        assert data["run_id"] == manifest.run_id
        assert "chunks" in data
        assert data["chunk_count"] == manifest.chunk_count

    def test_sqlite_db_written(self, tmp_path: Path) -> None:
        """ingest.db is written to the output directory."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        assert manifest.output_sqlite_path
        db_path = Path(manifest.output_sqlite_path)
        assert db_path.exists()

    def test_sqlite_contains_chunks(self, tmp_path: Path) -> None:
        """SQLite ingest.db contains rows in corpus_chunks table."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        db_path = Path(manifest.output_sqlite_path)  # type: ignore[arg-type]
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT COUNT(*) FROM corpus_chunks WHERE run_id = ?",
                (manifest.run_id,),
            ).fetchone()
        assert rows is not None
        assert rows[0] == manifest.chunk_count

    def test_empty_corpus_dir(self, tmp_path: Path) -> None:
        """Empty corpus directory produces a manifest with no documents or chunks."""
        empty_corpus = tmp_path / "empty"
        empty_corpus.mkdir()
        pipeline = IngestPipeline(
            corpus_dir=empty_corpus,
            metamodel_dir=empty_corpus,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        assert manifest.source_documents == []
        assert manifest.chunks == []
        assert manifest.errors == []

    def test_run_ids_are_unique(self, tmp_path: Path) -> None:
        """Two consecutive runs produce different run_ids."""
        pipeline = IngestPipeline(
            corpus_dir=FIXTURES_DIR,
            metamodel_dir=FIXTURES_DIR,
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        m1 = pipeline.run()
        m2 = pipeline.run()
        assert m1.run_id != m2.run_id

    def test_subdirectory_files_discovered_recursive(self, tmp_path: Path) -> None:
        """Files placed in corpus subdirectories are discovered and ingested."""
        corpus = tmp_path / "corpus"
        subdir = corpus / "domain_docs"
        subdir.mkdir(parents=True)
        (corpus / "top_level.txt").write_text(
            "Top-level corpus document with sufficient content.\n\n"
            "Second paragraph ensures at least one chunk is produced here."
        )
        (subdir / "nested.txt").write_text(
            "Nested document from a subdirectory.\n\n"
            "Another paragraph for the nested subdirectory document here."
        )
        pipeline = IngestPipeline(
            corpus_dir=corpus,
            metamodel_dir=tmp_path / "meta",
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        manifest = pipeline.run()
        ingested_names = {d.file_name for d in manifest.source_documents}
        assert "top_level.txt" in ingested_names
        assert "nested.txt" in ingested_names

    def test_non_recursive_skips_subdirectory_files(self, tmp_path: Path) -> None:
        """When recursive=False, files in subdirectories are not ingested."""
        corpus = tmp_path / "corpus"
        subdir = corpus / "inner"
        subdir.mkdir(parents=True)
        (corpus / "top.txt").write_text(
            "Top-level file with enough content for chunking.\n\n"
            "Second paragraph to confirm top-level is still ingested."
        )
        (subdir / "nested.txt").write_text(
            "Nested file that should be ignored in non-recursive mode.\n\n"
            "Second paragraph."
        )
        pipeline = IngestPipeline(
            corpus_dir=corpus,
            metamodel_dir=tmp_path / "meta",
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
            recursive=False,
        )
        manifest = pipeline.run()
        ingested_names = {d.file_name for d in manifest.source_documents}
        assert "top.txt" in ingested_names
        assert "nested.txt" not in ingested_names

    def test_doc_id_stable_across_runs(self, tmp_path: Path) -> None:
        """Re-ingesting the same file on a second run produces the same doc_id."""
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "stable.txt").write_text(
            "Stable content that never changes between runs.\n\n"
            "Second paragraph to ensure chunking produces output."
        )
        pipeline = IngestPipeline(
            corpus_dir=corpus,
            metamodel_dir=tmp_path / "meta",
            screenshots_dir=tmp_path / "screenshots",
            output_dir=tmp_path / "out",
        )
        m1 = pipeline.run()
        m2 = pipeline.run()
        ids_run1 = {d.file_name: d.doc_id for d in m1.source_documents}
        ids_run2 = {d.file_name: d.doc_id for d in m2.source_documents}
        assert ids_run1["stable.txt"] == ids_run2["stable.txt"]


@pytest.mark.integration
class TestBuildIngestor:
    def test_build_ingestor_returns_dispatcher(self) -> None:
        from ea_mbse_pipeline.ingest.pipeline import DispatchIngestor
        ingestor = build_ingestor()
        assert isinstance(ingestor, DispatchIngestor)

    def test_text_file_ingestible(self, tmp_path: Path) -> None:
        """build_ingestor().ingest() processes the text fixture."""
        ingestor = build_ingestor()
        fixture = FIXTURES_DIR / "sample_corpus.txt"
        raw = ingestor.ingest(fixture)
        assert raw.kind == InputKind.TEXT
        assert len(raw.text) > 0
        assert raw.source == fixture

    def test_unsupported_extension_raises(self, tmp_path: Path) -> None:
        from ea_mbse_pipeline.shared.errors import PipelineError, ErrorCode
        ingestor = build_ingestor()
        fake = tmp_path / "data.bin"
        fake.write_bytes(b"\x00\x01\x02")
        with pytest.raises(PipelineError) as exc_info:
            ingestor.ingest(fake)
        assert exc_info.value.code == ErrorCode.INGEST_UNSUPPORTED_FORMAT
