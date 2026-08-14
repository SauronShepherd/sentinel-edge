"""At-rest protection contract for restricted local evidence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocalEvidenceProtection:
    deployment_id: str
    copied_powered_off_media_in_scope: bool
    encryption_mode: str
    key_authority: str
    evidence_volume: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.deployment_id, self.encryption_mode, self.key_authority, self.evidence_volume)):
            raise ValueError("deployment, encryption, key authority and evidence volume are required")
        if self.encryption_mode not in {"full-disk", "application-authenticated"}:
            raise ValueError("qualified encryption mode is required")
        if self.key_authority == self.evidence_volume:
            raise ValueError("key authority must be separate from evidence volume")

    def copied_volume_access(self, *, supplied_key_authority: str | None) -> bool:
        return supplied_key_authority == self.key_authority

    def threat_profile(self) -> dict[str, object]:
        return {"deployment_id": self.deployment_id, "copied_powered_off_media_in_scope": self.copied_powered_off_media_in_scope, "encryption_mode": self.encryption_mode, "key_authority": self.key_authority, "evidence_volume": self.evidence_volume}
