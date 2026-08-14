"""Offline research context explicitly separated from local event truth."""

from pydantic import BaseModel, ConfigDict, model_validator


class ResearchContextRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_name: str
    record_id: str
    original_provenance: str
    offline_fixture: bool = True
    local_event_truth: bool = False
    decision_influence_allowed: bool = False

    @model_validator(mode="after")
    def validate_scope(self) -> "ResearchContextRecord":
        if any(not value.strip() for value in (self.dataset_name, self.record_id, self.original_provenance)):
            raise ValueError("research context identity and provenance are required")
        if self.local_event_truth or self.decision_influence_allowed:
            raise ValueError("research context cannot become local event truth or decision input")
        if not self.offline_fixture:
            raise ValueError("research context must be an offline fixture")
        return self
