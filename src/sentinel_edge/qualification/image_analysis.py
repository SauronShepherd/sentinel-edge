"""Bounded visual/OCR result contract."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ImageRegion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class BoundedImageAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str
    regions: tuple[ImageRegion, ...] = ()
    text: tuple[str, ...] = ()
    ocr_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    quality_flags: tuple[str, ...] = ()
    abstained: bool

    @model_validator(mode="after")
    def validate_result(self) -> "BoundedImageAnalysis":
        if not self.profile_id.strip():
            raise ValueError("bounded image profile is required")
        if self.abstained and not self.quality_flags:
            raise ValueError("abstention requires a quality flag")
        if self.text and self.ocr_confidence is None:
            raise ValueError("OCR text requires confidence")
        return self
