"""Configured pre-persistence transforms for sensitive multimodal fields."""

from pydantic import BaseModel, ConfigDict, Field


class PrePersistenceTransform(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    blur_faces: bool = True
    blur_plates: bool = True
    coordinate_precision_digits: int = Field(default=3, ge=0, le=6)
    redact_private_sender_identity: bool = True

    def apply(self, *, coordinates: tuple[float, float] | None = None,
              sender_identity: str | None = None) -> dict[str, object]:
        result: dict[str, object] = {
            "faces_transformed": self.blur_faces,
            "plates_transformed": self.blur_plates,
            "private_sender_identity_transformed": self.redact_private_sender_identity and sender_identity is not None,
        }
        if coordinates is not None:
            result["coordinates"] = tuple(round(value, self.coordinate_precision_digits) for value in coordinates)
        if sender_identity is not None:
            result["sender_identity"] = "redacted" if self.redact_private_sender_identity else sender_identity
        return result
