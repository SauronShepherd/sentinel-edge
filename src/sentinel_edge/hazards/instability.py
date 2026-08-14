from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstabilityMetadata:
    available: bool
    score: float | None
    uncertainty: float | None
    profile_id: str | None
    reason_code: str

    @classmethod
    def unavailable(cls, reason: str = "instability_not_applicable") -> "InstabilityMetadata":
        return cls(False, None, None, None, reason)

    @classmethod
    def from_prediction(cls, score: float, *, uncertainty: float, profile_id: str) -> "InstabilityMetadata":
        if not 0.0 <= score <= 1.0 or not 0.0 <= uncertainty <= 1.0 or not profile_id.strip():
            raise ValueError("instability score, uncertainty, and profile are required")
        return cls(True, score, uncertainty, profile_id, "validated_instability_available")

    def feature_values(self) -> dict[str, float]:
        return {
            "instability_available": float(self.available),
            "instability_score": self.score or 0.0,
            "instability_uncertainty": self.uncertainty or 0.0,
        }
