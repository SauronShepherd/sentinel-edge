"""Structured machine finding contract; findings remain evidence, not facts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StructuredFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_id: str
    subject: str
    predicate: str
    object_or_value: str
    event_time: datetime | None = None
    location: str | None = None
    uncertainty: float = Field(ge=0.0, le=1.0)
    source_evidence_id: str

    @model_validator(mode="after")
    def validate_finding(self) -> "StructuredFinding":
        if any(not value.strip() for value in (self.finding_id, self.subject, self.predicate, self.object_or_value, self.source_evidence_id)):
            raise ValueError("structured finding identity and subject/predicate/value are required")
        if self.event_time is not None and (self.event_time.tzinfo is None or self.event_time.utcoffset() is None):
            raise ValueError("event_time must be timezone-aware")
        return self
