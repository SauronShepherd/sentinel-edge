"""Metadata contract for static raster context, never represented as local measurement."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StaticRasterContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    resolution_m: float = Field(gt=0.0)
    uncertainty: float = Field(ge=0.0)
    context_only: bool = True
    display_label: str = "static context; not an exact local measurement"

    @model_validator(mode="after")
    def preserve_context_boundary(self) -> "StaticRasterContext":
        if not self.source_id.strip():
            raise ValueError("static raster source_id must not be blank")
        if not self.context_only:
            raise ValueError("static raster context cannot be represented as local measurement")
        if "not an exact local measurement" not in self.display_label.lower():
            raise ValueError("static raster display must disclose context-only limitation")
        return self

