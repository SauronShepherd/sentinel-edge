"""Privacy-aware, time-varying location evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LocationEvidence:
    subject: str
    observed_at: datetime
    latitude: float
    longitude: float
    precision_m: float
    derivation: str
    privacy_class: str
    consent_basis: str | None

    def __post_init__(self) -> None:
        if not self.subject.strip() or not self.derivation.strip() or not self.privacy_class.strip():
            raise ValueError("location evidence identity and derivation are required")
        if self.observed_at.tzinfo is None or self.precision_m <= 0:
            raise ValueError("location evidence requires timezone-aware time and positive precision")
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            raise ValueError("location coordinates out of bounds")
        if self.privacy_class in {"restricted", "private"} and not self.consent_basis:
            raise ValueError("restricted location evidence requires consent basis")

    def as_evidence(self) -> dict[str, object]:
        return {"subject": self.subject, "observed_at": self.observed_at.isoformat(), "latitude": self.latitude, "longitude": self.longitude, "precision_m": self.precision_m, "derivation": self.derivation, "privacy_class": self.privacy_class, "consent_basis": self.consent_basis}
