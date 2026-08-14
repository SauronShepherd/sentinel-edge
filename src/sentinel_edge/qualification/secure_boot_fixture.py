"""Exact secure-boot fixture verification and private-key recovery boundary."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecureBootFixture:
    board_model: str
    eeprom_config_digest: str
    signed_boot_image_digest: str
    key_lifecycle_ref: str
    recovery_procedure_ref: str
    signature_valid: bool
    key_matches: bool
    rollback_detected: bool
    recovery_exposes_private_key: bool = False

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.board_model, self.eeprom_config_digest, self.signed_boot_image_digest, self.key_lifecycle_ref, self.recovery_procedure_ref)):
            raise ValueError("secure-boot fixture identity and lifecycle fields are required")
        if self.recovery_exposes_private_key:
            raise ValueError("recovery procedure must not expose signing private key")

    def boot_allowed(self) -> bool:
        return self.signature_valid and self.key_matches and not self.rollback_detected
