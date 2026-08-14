"""Synthetic, offline judge backup/restore fixture contract."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeRestoreFixture:
    fixture_id: str
    synthetic_content: bool
    offline_verification_material: str
    private_decryption_requirement: bool = False

    def __post_init__(self) -> None:
        if not self.fixture_id.strip() or not self.offline_verification_material.strip():
            raise ValueError("fixture identity and public verification material are required")
        if not self.synthetic_content:
            raise ValueError("judge restore fixtures must contain synthetic content")
        if self.private_decryption_requirement:
            raise ValueError("judge restore cannot require hidden private decryption")

    def restore_ready(self) -> bool:
        return True
