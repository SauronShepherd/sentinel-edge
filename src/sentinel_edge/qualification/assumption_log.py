"""Append-only hazard and assumption records for qualification/Judge Proof."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class AssumptionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=1)
    assumption_id: str
    hazard_id: str
    statement: str
    owner: str
    resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssumptionLog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    records: tuple[AssumptionRecord, ...] = ()

    def append(self, record: AssumptionRecord) -> "AssumptionLog":
        if self.records and record.sequence != self.records[-1].sequence + 1:
            raise ValueError("assumption log sequence must be append-only and contiguous")
        if any(item.assumption_id == record.assumption_id for item in self.records):
            raise ValueError("assumption identifiers cannot be rewritten or duplicated")
        return AssumptionLog(records=self.records + (record,))

    def unresolved_for_judge_proof(self) -> tuple[dict[str, object], ...]:
        return tuple(item.model_dump(mode="json") for item in self.records if not item.resolved)

