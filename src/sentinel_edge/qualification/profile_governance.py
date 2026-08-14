"""Bounded governance record for suspect or expired profiles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ProfileGovernance:
    profile_id: str
    owner: str
    review_deadline: datetime
    interim_effect: str
    rollback_profile: str

    def __post_init__(self) -> None:
        if not self.profile_id.strip() or not self.owner.strip() or not self.interim_effect.strip() or not self.rollback_profile.strip():
            raise ValueError("profile governance fields are required")
        if self.review_deadline.tzinfo is None:
            raise ValueError("review deadline must be timezone-aware")

    def active_at(self, now: datetime) -> bool:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return now < self.review_deadline

    def decision(self, now: datetime) -> str:
        return self.interim_effect if self.active_at(now) else f"rollback:{self.rollback_profile}"
