"""Admission controls for research/teacher-only GeoAI assets."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AssetUse(StrEnum):
    OFFLINE = "offline"
    TEACHER = "teacher"
    EVALUATION_ONLY = "evaluation_only"
    RELEASED = "released"


@dataclass(frozen=True)
class ResearchAssetPolicy:
    asset_id: str
    use: AssetUse = AssetUse.OFFLINE
    promotion_gate_passed: bool = False

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("asset_id is required")
        if self.use is AssetUse.RELEASED and not self.promotion_gate_passed:
            raise ValueError("released asset requires promotion gate")
        if self.promotion_gate_passed and self.use is not AssetUse.RELEASED:
            raise ValueError("promoted asset must be marked released")

    def permits_incident_state(self) -> bool:
        return self.use is AssetUse.RELEASED and self.promotion_gate_passed

    def permits_h0_quality_claim(self) -> bool:
        return self.permits_incident_state()

    def assert_not_authoritative(self) -> None:
        if not self.permits_incident_state():
            raise PermissionError("research asset is not authoritative for incident state or H0 claims")
