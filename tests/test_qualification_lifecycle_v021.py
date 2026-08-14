from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from sentinel_edge.domain.models import CapabilityState
from sentinel_edge.qualification import (
    EvidenceProvenance,
    QualificationClaim,
    QualificationDomain,
    QualificationEvidenceWindow,
    enforce_claim_ceiling,
    evaluate_evidence_window,
    qualification_vocabulary_report,
)

NOW = datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)


def _window(**overrides):
    values = dict(
        qualification_id="host-rpi5-v1",
        domain=QualificationDomain.PLATFORM,
        subject_id="rpi5-001",
        state=CapabilityState.TARGET_QUALIFIED,
        evidence_sha256="a" * 64,
        valid_from=NOW - timedelta(days=1),
        valid_until=NOW + timedelta(days=1),
        provenance=EvidenceProvenance.OBSERVED,
        target_binding_sha256="b" * 64,
    )
    values.update(overrides)
    return QualificationEvidenceWindow(**values)


def test_expired_qualification_blocks_claim() -> None:
    report = evaluate_evidence_window(_window(valid_until=NOW), now=NOW)
    assert report["effective_state"] == "expired"
    assert report["claim_allowed"] is False
    assert "qualification_expired" in report["failures"]


def test_claim_cannot_exceed_weakest_evidence() -> None:
    platform = evaluate_evidence_window(_window(), now=NOW)
    model = evaluate_evidence_window(_window(
        qualification_id="model-v1", domain=QualificationDomain.MODEL,
        state=CapabilityState.TESTED, subject_id="model", evidence_sha256="c"*64,
    ), now=NOW)
    decision = enforce_claim_ceiling(
        QualificationClaim(capability_id="seismic", requested_state=CapabilityState.TARGET_QUALIFIED, statement="Target qualified"),
        [platform, model],
    )
    assert decision["allowed"] is False
    assert decision["evidence_ceiling"] == "tested"


def test_reconstructed_evidence_cannot_invent_qualification() -> None:
    with pytest.raises(ValidationError):
        _window(
            provenance=EvidenceProvenance.RECONSTRUCTED,
            reconstructed_missing_fields=("original_timestamp",),
        )
    report = evaluate_evidence_window(_window(
        state=CapabilityState.TESTED,
        provenance=EvidenceProvenance.RECONSTRUCTED,
        reconstructed_missing_fields=("original_timestamp", "target_binding"),
    ), now=NOW)
    assert report["claim_allowed"] is False
    assert "historical_proof_incomplete" in report["failures"]


def test_vocabulary_is_generated_and_closed() -> None:
    report = qualification_vocabulary_report()
    assert report["unknown_values_rejected"] is True
    assert report["states"] == [state.value for state in CapabilityState]
