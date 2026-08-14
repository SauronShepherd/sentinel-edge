"""Minimal lock-screen notification projection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LockScreenNotification:
    title: str
    body: str
    sensitive_details_hidden: bool


def lock_screen_notification(*, hazard: str, state: str, sensitive: bool = True) -> LockScreenNotification:
    if not hazard.strip() or not state.strip():
        raise ValueError("hazard and state are required")
    if sensitive:
        return LockScreenNotification("Sentinel Edge alert", "Open Sentinel Edge for details", True)
    return LockScreenNotification(f"Sentinel Edge: {hazard}", state, False)
