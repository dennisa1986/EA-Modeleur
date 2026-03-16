"""Structured error codes and base exception for the MBSE pipeline.

Every pipeline exception must subclass PipelineError and carry an ErrorCode.
Never raise bare Exception or ValueError inside pipeline code.
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    # Ingestion
    INGEST_UNSUPPORTED_FORMAT   = "INGEST-001"
    INGEST_READ_FAILURE         = "INGEST-002"
    INGEST_EMPTY_CONTENT        = "INGEST-003"

    # Metamodel
    METAMODEL_PARSE_ERROR       = "META-001"
    METAMODEL_INVALID_XMI       = "META-002"
    METAMODEL_RULE_COMPILE_FAIL = "META-003"

    # Canonical model
    CANONICAL_SCHEMA_VIOLATION  = "CANON-001"
    CANONICAL_MISSING_PROVENANCE= "CANON-002"

    # Validation
    VALIDATION_RULE_ERROR       = "VAL-001"
    VALIDATION_HARD_STOP        = "VAL-002"

    # Serialization
    SERIAL_UNMAPPABLE_ELEMENT   = "SER-001"
    SERIAL_XMI_BUILD_FAIL       = "SER-002"

    # EA test
    EA_TEST_IMPORT_FAIL         = "EATEST-001"
    EA_TEST_GOLDEN_MISMATCH     = "EATEST-002"

    # Orchestration
    ORCH_STAGE_FAILED           = "ORCH-001"
    ORCH_CONFIG_INVALID         = "ORCH-002"


class PipelineError(Exception):
    """Base class for all pipeline exceptions."""

    def __init__(self, code: ErrorCode, message: str, *, context: dict | None = None) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.context: dict = context or {}
