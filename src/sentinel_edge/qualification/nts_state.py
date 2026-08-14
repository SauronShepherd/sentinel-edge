"""RFC 8915 NTS authentication state and explicit fallback semantics."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NtsState:
    authentication_succeeded: bool
    failure_reason: str | None = None
    fallback_mode: str | None = None
    trusted_status: bool = False

    def __post_init__(self) -> None:
        if not self.authentication_succeeded and not self.failure_reason:
            raise ValueError("NTS failure reason is required")
        if self.fallback_mode and self.trusted_status:
            raise ValueError("fallback cannot silently preserve trusted status")

    def decision(self) -> dict[str, object]:
        return {"nts_authenticated": self.authentication_succeeded, "failure_reason": self.failure_reason, "fallback_mode": self.fallback_mode, "trusted_status": self.trusted_status}
