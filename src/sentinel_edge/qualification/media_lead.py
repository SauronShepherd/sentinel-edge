"""Metadata/embed leads separated from lawful supplied-media acquisition."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, AnyHttpUrl, model_validator


class MediaLeadDisposition(StrEnum):
    METADATA_ONLY = "metadata_only"
    SUPPLIED_MEDIA_UPLOAD = "supplied_media_upload"
    DOWNLOAD_BLOCKED = "download_blocked"


class MediaLead(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    platform: str
    canonical_url: AnyHttpUrl
    disposition: MediaLeadDisposition
    media_bytes_retained: bool = False
    enrollment_id: str | None = None

    @model_validator(mode="after")
    def validate_lead(self) -> "MediaLead":
        if not self.platform.strip():
            raise ValueError("media lead platform is required")
        if self.disposition is MediaLeadDisposition.METADATA_ONLY and self.media_bytes_retained:
            raise ValueError("metadata lead cannot retain media bytes")
        if self.disposition is MediaLeadDisposition.SUPPLIED_MEDIA_UPLOAD and not self.enrollment_id:
            raise ValueError("supplied media upload requires enrollment")
        if self.disposition is MediaLeadDisposition.DOWNLOAD_BLOCKED and self.media_bytes_retained:
            raise ValueError("blocked download cannot retain media bytes")
        return self
