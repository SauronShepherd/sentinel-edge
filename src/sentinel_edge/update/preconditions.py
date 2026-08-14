"""Activation preconditions that fail closed before changing the active release."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationPreconditions:
    power_ok: bool
    storage_ok: bool
    compatible: bool

    @property
    def safe(self) -> bool:
        return self.power_ok and self.storage_ok and self.compatible

    def require_safe(self) -> tuple[str, ...]:
        failures = tuple(name for name, ok in (("power", self.power_ok), ("storage", self.storage_ok), ("compatibility", self.compatible)) if not ok)
        if failures:
            raise ValueError("activation preconditions failed: " + ",".join(failures))
        return ("power_ok", "storage_ok", "compatibility_ok")
