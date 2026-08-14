"""Versioned source snapshot timing contract."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


class SourceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema: str = "sentinel-edge-source-snapshot/1.0"
    source_id: str
    observed_at: datetime
    published_at: datetime
    fetched_at: datetime
    expires_at: datetime
    payload_sha256: str

    @model_validator(mode="after")
    def validate_timeline(self) -> "SourceSnapshot":
        if not self.source_id.strip():
            raise ValueError("source_id must not be blank")
        if not self.payload_sha256 or len(self.payload_sha256) != 64:
            raise ValueError("payload_sha256 must be a SHA-256 digest")
        if self.published_at < self.observed_at:
            raise ValueError("published_at cannot precede observed_at")
        if self.fetched_at < self.published_at:
            raise ValueError("fetched_at cannot precede published_at")
        if self.expires_at <= self.fetched_at:
            raise ValueError("expires_at must follow fetched_at")
        return self
