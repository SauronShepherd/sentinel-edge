"""Preserve authoritative source wording and severity as immutable fields."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OfficialSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema: str = "sentinel-edge-official-source-record/1.0"
    source_id: str
    original_wording: str = Field(min_length=1)
    official_severity: str = Field(min_length=1)
    derived_summary: str | None = None

    def display_text(self) -> str:
        """Return source wording; summaries never replace the official text."""
        return self.original_wording
