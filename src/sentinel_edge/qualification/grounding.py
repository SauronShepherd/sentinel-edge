"""Evidence-based geotemporal grounding provenance."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GroundingSource(StrEnum):
    CLAIMED = "claimed"
    METADATA_DERIVED = "metadata_derived"
    VISUALLY_INFERRED = "visually_inferred"
    OPERATOR_CONFIRMED = "operator_confirmed"


class GroundedValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str
    value: str
    source: GroundingSource
    confidence: float = Field(ge=0.0, le=1.0)
    source_evidence_id: str
    confirmed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_grounding(self) -> "GroundedValue":
        if not self.field.strip() or not self.value.strip() or not self.source_evidence_id.strip():
            raise ValueError("grounded field, value, and evidence id are required")
        if self.confirmed_at is not None and (self.confirmed_at.tzinfo is None or self.confirmed_at.utcoffset() is None):
            raise ValueError("confirmed_at must be timezone-aware")
        if self.source is GroundingSource.OPERATOR_CONFIRMED and self.confirmed_at is None:
            raise ValueError("operator-confirmed grounding requires confirmation time")
        return self
