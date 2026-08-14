"""Admission contract for separately signed custom native-code artifacts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NativeArtifactQualification:
    artifact_digest: str
    signature_ref: str
    abi_evidence: str
    compiler_evidence: str
    hardening_evidence: str
    sandbox_evidence: str
    attack_evidence: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.artifact_digest, self.signature_ref, self.abi_evidence, self.compiler_evidence, self.hardening_evidence, self.sandbox_evidence, self.attack_evidence)):
            raise ValueError("signed native artifact requires complete qualification evidence")

    def activation_allowed(self) -> bool:
        return True

    def as_receipt(self) -> dict[str, str | bool]:
        return {"artifact_digest": self.artifact_digest, "signature_ref": self.signature_ref, "abi_evidence": self.abi_evidence, "compiler_evidence": self.compiler_evidence, "hardening_evidence": self.hardening_evidence, "sandbox_evidence": self.sandbox_evidence, "attack_evidence": self.attack_evidence, "activation_allowed": True}
