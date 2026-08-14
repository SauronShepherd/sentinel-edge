"""Versioned multimodal evidence envelope for fixture and governed ingest."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceModality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class MultimodalEvidenceEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "sentinel-edge-multimodal-evidence/1.0"
    evidence_id: str
    modality: EvidenceModality
    origin: str
    captured_at: datetime
    received_at: datetime
    rights_basis: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_envelope(self) -> "MultimodalEvidenceEnvelope":
        if not self.evidence_id.strip() or not self.origin.strip() or not self.rights_basis.strip():
            raise ValueError("evidence identity, origin, and rights basis are required")
        if self.captured_at.tzinfo is None or self.received_at.tzinfo is None:
            raise ValueError("evidence timestamps must be timezone-aware")
        if self.received_at < self.captured_at:
            raise ValueError("received_at cannot precede captured_at")
        return self
