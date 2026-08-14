"""Component-independent update rollback and anti-rollback policy."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateBundle:
    bundle_type: str
    version: int
    rollback_version: int
    digest: str


@dataclass(frozen=True)
class RollbackDecision:
    accepted: bool
    action: str
    reason: str


def evaluate_update(*, active: UpdateBundle, candidate: UpdateBundle, canary_passed: bool) -> RollbackDecision:
    if candidate.version < active.version and candidate.version < active.rollback_version:
        return RollbackDecision(False, "reject", "anti_rollback_floor")
    if candidate.version == active.version and candidate.digest == active.digest:
        return RollbackDecision(False, "reject", "replay")
    if not canary_passed:
        return RollbackDecision(False, "restore_last_known_good", "canary_failed")
    return RollbackDecision(True, "activate", "verified_and_canary_passed")
