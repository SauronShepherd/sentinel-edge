"""Traceability from derived claims and retained bytes to governed sources."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DerivedArtifactKind(StrEnum):
    CLAIM = "claim"
    RETAINED_BYTES = "retained_bytes"


class GovernedLineageLink(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str
    artifact_kind: DerivedArtifactKind
    governed_source_item_id: str
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transformation_id: str

    @model_validator(mode="after")
    def validate_link(self) -> "GovernedLineageLink":
        if any(not value.strip() for value in (self.artifact_id, self.governed_source_item_id, self.transformation_id)):
            raise ValueError("lineage identity and transformation are required")
        return self
