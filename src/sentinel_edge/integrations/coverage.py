"""Declared source coverage dimensions for scientific-data health."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    expected_spatial: int | None = Field(default=None, ge=0)
    received_spatial: int | None = Field(default=None, ge=0)
    expected_temporal: int | None = Field(default=None, ge=0)
    received_temporal: int | None = Field(default=None, ge=0)
    expected_pages: int | None = Field(default=None, ge=0)
    received_pages: int | None = Field(default=None, ge=0)
    expected_tiles: int | None = Field(default=None, ge=0)
    received_tiles: int | None = Field(default=None, ge=0)
    expected_contributors: int | None = Field(default=None, ge=0)
    received_contributors: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_coverage(self) -> "SourceCoverage":
        if not self.source_id.strip():
            raise ValueError("source_id must not be blank")
        pairs = (
            ("spatial", self.expected_spatial, self.received_spatial),
            ("temporal", self.expected_temporal, self.received_temporal),
            ("pages", self.expected_pages, self.received_pages),
            ("tiles", self.expected_tiles, self.received_tiles),
            ("contributors", self.expected_contributors, self.received_contributors),
        )
        for name, expected, received in pairs:
            if expected is not None and received is not None and received > expected:
                raise ValueError(f"received {name} coverage cannot exceed expected coverage")
        return self

    def missing_dimensions(self) -> tuple[str, ...]:
        pairs = {
            "spatial": (self.expected_spatial, self.received_spatial),
            "temporal": (self.expected_temporal, self.received_temporal),
            "pages": (self.expected_pages, self.received_pages),
            "tiles": (self.expected_tiles, self.received_tiles),
            "contributors": (self.expected_contributors, self.received_contributors),
        }
        return tuple(name for name, (expected, received) in pairs.items() if expected is None or received is None or received < expected)

