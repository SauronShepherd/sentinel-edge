"""Authorized platform metadata and availability contract."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlatformAccessStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    platform: str
    creator_or_research_eligible: bool
    api_lag_seconds: float | None = Field(default=None, ge=0.0)
    media_bytes_available: bool
    real_time_assumed: bool = False
    access_basis: str

    @model_validator(mode="after")
    def validate_status(self) -> "PlatformAccessStatus":
        if not self.platform.strip() or not self.access_basis.strip():
            raise ValueError("platform and access basis are required")
        if self.real_time_assumed:
            raise ValueError("platform access must not assume real-time availability")
        if self.media_bytes_available and not self.creator_or_research_eligible:
            raise ValueError("media bytes require an eligible authorized access path")
        return self
