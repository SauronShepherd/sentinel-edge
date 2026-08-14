from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthorityWatermark(BaseModel):
    """Canonical authority prefix represented by a derived product surface."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_id: str = Field(default="sentinel-edge-authority-watermark/1.0", alias="schema")
    epoch_id: str
    highest_contiguous_position: int = Field(ge=0)
    accepted_event_count: int = Field(ge=0)
    valid: bool
    failures: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_watermark(self) -> "AuthorityWatermark":
        if not self.epoch_id.strip():
            raise ValueError("authority watermark epoch_id must not be blank")
        if self.valid and self.failures:
            raise ValueError("valid authority watermark cannot carry failures")
        if not self.valid and self.highest_contiguous_position != 0:
            raise ValueError("invalid authority watermark must fail closed at position zero")
        return self

    @classmethod
    def from_conformance(cls, conformance: dict[str, Any]) -> "AuthorityWatermark":
        return cls(
            epoch_id=str(conformance.get("epoch_id", "unknown")),
            highest_contiguous_position=int(conformance.get("highest_contiguous_position", 0)),
            accepted_event_count=int(conformance.get("event_count", 0)),
            valid=bool(conformance.get("valid", False)),
            failures=tuple(str(item) for item in conformance.get("failures", ())),
        )
