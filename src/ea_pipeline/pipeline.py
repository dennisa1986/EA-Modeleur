"""PipelineOrchestrator — wires all stages via dependency injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ea_pipeline.canonical.protocols import CanonicalModelBuilderProtocol
from ea_pipeline.import_validation.protocols import ImportValidatorProtocol
from ea_pipeline.ingestion.protocols import IngestorProtocol
from ea_pipeline.metamodel.protocols import MetamodelCompilerProtocol
from ea_pipeline.serialization.protocols import SerializerProtocol
from ea_pipeline.validation.protocols import ValidatorProtocol


@dataclass
class PipelineResult:
    """Aggregated result produced by one full pipeline run."""

    canonical_model: dict[str, Any] = field(default_factory=dict)
    validation_report: dict[str, Any] = field(default_factory=dict)
    serialized_artefact: bytes = b""
    import_report: dict[str, Any] = field(default_factory=dict)
    success: bool = False


class PipelineOrchestrator:
    """Runs raw input through all pipeline stages in order.

    All stages are injected at construction time; no stage is instantiated
    internally.  This makes each stage independently replaceable and testable.
    """

    def __init__(
        self,
        ingestor: IngestorProtocol,
        metamodel_compiler: MetamodelCompilerProtocol,
        canonical_builder: CanonicalModelBuilderProtocol,
        validator: ValidatorProtocol,
        serializer: SerializerProtocol,
        import_validator: ImportValidatorProtocol,
    ) -> None:
        self._ingestor = ingestor
        self._metamodel_compiler = metamodel_compiler
        self._canonical_builder = canonical_builder
        self._validator = validator
        self._serializer = serializer
        self._import_validator = import_validator

    def run(self, raw_input: Any) -> PipelineResult:  # noqa: ANN401
        """Execute the full pipeline on *raw_input* and return a PipelineResult."""
        raise NotImplementedError
