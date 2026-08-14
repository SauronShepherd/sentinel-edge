"""Exact machine-readable release capability profile."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CapabilityState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    EMULATED = "emulated"
    FIXTURE_ONLY = "fixture_only"
    DEGRADED = "degraded"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class Capability:
    name: str
    state: CapabilityState
    reason: str


@dataclass(frozen=True)
class ReleaseProfile:
    profile_id: str
    capabilities: tuple[Capability, ...]

    def __post_init__(self) -> None:
        required = {item.value for item in CapabilityState}
        states = {item.state.value for item in self.capabilities}
        if not self.profile_id.strip() or states != required:
            raise ValueError("release profile must enumerate every capability state")
        if len({item.name for item in self.capabilities}) != len(self.capabilities):
            raise ValueError("release profile capability names must be unique")
        if any(not item.name.strip() or not item.reason.strip() for item in self.capabilities):
            raise ValueError("release profile entries require name and reason")

    def as_dict(self) -> dict[str, Any]:
        return {"schema": "sentinel-edge-release-profile/1.0", "profile_id": self.profile_id, "capabilities": [item.__dict__ | {"state": item.state.value} for item in self.capabilities]}
