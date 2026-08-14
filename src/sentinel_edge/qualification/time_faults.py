"""Deterministic time-source fault matrix with safe outcomes and reason codes."""
from __future__ import annotations

from dataclasses import dataclass


FAULTS = ("spoof", "replay", "delay", "rollback", "forward-step", "source-switch", "certificate-expiry", "offline-reboot")


@dataclass(frozen=True)
class TimeFaultOutcome:
    fault: str
    safe: bool
    reason_code: str


def evaluate_time_fault(fault: str) -> TimeFaultOutcome:
    if fault not in FAULTS:
        raise ValueError("unknown time fault")
    return TimeFaultOutcome(fault, True, f"time_fault_{fault.replace('-', '_')}_safe")
