"""Typed optional learned-forecast metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastMetadata:
    available: bool
    score: float | None
    horizon_seconds: int | None
    uncertainty: float | None
    profile_id: str | None
    reason_code: str

    @classmethod
    def unavailable(cls, reason_code: str = "forecast_not_applicable") -> "ForecastMetadata":
        return cls(False, None, None, None, None, reason_code)

    @classmethod
    def from_prediction(
        cls,
        score: float,
        *,
        horizon_seconds: int,
        uncertainty: float,
        profile_id: str,
    ) -> "ForecastMetadata":
        if not 0.0 <= score <= 1.0:
            raise ValueError("forecast score outside [0,1]")
        if horizon_seconds <= 0 or not 0.0 <= uncertainty <= 1.0 or not profile_id.strip():
            raise ValueError("forecast horizon, uncertainty, and profile are required")
        return cls(True, score, horizon_seconds, uncertainty, profile_id, "validated_forecast_available")

    def feature_values(self) -> dict[str, float]:
        if not self.available:
            return {"forecast_available": 0.0}
        assert self.score is not None and self.horizon_seconds is not None and self.uncertainty is not None
        return {
            "forecast_available": 1.0,
            "forecast_score": self.score,
            "forecast_horizon_seconds": float(self.horizon_seconds),
            "forecast_uncertainty": self.uncertainty,
        }
