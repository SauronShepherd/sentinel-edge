"""Explicit upload-to-analysis envelope boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinel_edge.domain.models import Observation
from sentinel_edge.evolution.contracts import ObservationContractReport, validate_observation_contract


@dataclass(frozen=True)
class UploadedEvidenceEnvelope:
    upload_sha256: str
    observation: Observation
    contract: ObservationContractReport

    @property
    def analysis_allowed(self) -> bool:
        return self.contract.valid


def normalize_uploaded_envelope(*, upload_sha256: str, payload: dict[str, Any]) -> UploadedEvidenceEnvelope:
    if len(upload_sha256) != 64 or any(c not in "0123456789abcdef" for c in upload_sha256.lower()):
        raise ValueError("upload digest is required before analysis")
    observation = Observation.model_validate(payload)
    contract = validate_observation_contract(observation)
    return UploadedEvidenceEnvelope(upload_sha256, observation, contract)
