from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True, slots=True)
class AcquisitionPolicy:
    permitted_use: bool
    retention_until: datetime | None = None
    analysis_authorized: bool = True
    privacy_approved: bool = True

    def authorize(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        if not self.permitted_use: raise PermissionError("use_not_permitted")
        if not self.analysis_authorized: raise PermissionError("analysis_not_authorized")
        if not self.privacy_approved: raise PermissionError("privacy_not_approved")
        if self.retention_until is not None and self.retention_until <= now: raise PermissionError("retention_expired")

