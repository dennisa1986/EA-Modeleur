"""PipelineOrchestrator — composes all stages and drives a full pipeline run."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ea_mbse_pipeline.canonical.protocols import CanonicalBuilderProtocol
from ea_mbse_pipeline.ea_test.protocols import EATesterProtocol
from ea_mbse_pipeline.ingest.protocols import IngestorProtocol
from ea_mbse_pipeline.metamodel.protocols import MetamodelCompilerProtocol
from ea_mbse_pipeline.retrieval.protocols import RetrieverProtocol
from ea_mbse_pipeline.serialization.protocols import SerializerProtocol
from ea_mbse_pipeline.validation.protocols import ValidatorProtocol

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Aggregated result of one full pipeline run."""

    success: bool = False
    canonical_model: dict[str, Any] = field(default_factory=dict)
    validation_passed: bool = False
    serialized_filename: str = ""
    ea_test_importable: bool = False
    errors: list[str] = field(default_factory=list)


class PipelineOrchestrator:
    """Runs raw input through all pipeline stages in order.

    All stages are injected at construction time.
    """

    def __init__(
        self,
        ingestor: IngestorProtocol,
        metamodel_compiler: MetamodelCompilerProtocol,
        canonical_builder: CanonicalBuilderProtocol,
        retriever: RetrieverProtocol,
        validator: ValidatorProtocol,
        serializer: SerializerProtocol,
        ea_tester: EATesterProtocol,
        xmi_path: Path,
        golden_dir: Path | None = None,
    ) -> None:
        self._ingestor = ingestor
        self._metamodel_compiler = metamodel_compiler
        self._canonical_builder = canonical_builder
        self._retriever = retriever
        self._validator = validator
        self._serializer = serializer
        self._ea_tester = ea_tester
        self._xmi_path = xmi_path
        self._golden_dir = golden_dir

    def run(self, source: Path) -> PipelineResult:
        """Execute the full pipeline on *source* and return a PipelineResult."""
        raise NotImplementedError("PipelineOrchestrator.run() — milestone: Sprint 1")
