"""Serialization stage output models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class SerializationFormat(StrEnum):
    XMI = "xmi"
    CSV = "csv"


class SerializedArtefact(BaseModel):
    format: SerializationFormat
    content: bytes
    filename: str
    """Suggested filename including extension, e.g. 'model.xmi'."""
    element_count: int = 0
    """Number of elements serialised — used by EA Test for sanity checks."""
