"""Media health capability disclosure; unavailable hardware data is explicit."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MediaKind(StrEnum):
    SSD = "ssd"
    EMMC = "emmc"
    SD = "sd"
    UNKNOWN = "unknown"


class MediaHealthCapability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: MediaKind
    device: str
    smart_available: bool
    endurance_available: bool
    health_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    limitation: str

    @model_validator(mode="after")
    def validate_disclosure(self) -> "MediaHealthCapability":
        if not self.device.strip() or not self.limitation.strip():
            raise ValueError("device and capability limitation disclosure are required")
        if self.health_percent is not None and not (self.smart_available or self.endurance_available):
            raise ValueError("health percentage requires an available capability")
        return self
