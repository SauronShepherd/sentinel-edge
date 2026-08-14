import pytest
from pydantic import ValidationError

from sentinel_edge.qualification.ood import OODDecision, OODDisposition


def test_ood_input_can_only_degrade_or_require_review() -> None:
    decision = OODDecision(
        input_id="camera-frame-17",
        baseline_confidence=0.8,
        observed_confidence=0.3,
        out_of_distribution=True,
        disposition=OODDisposition.REVIEW_REQUIRED,
        coverage="degraded",
        reason_codes=("ood_distance_high",),
    )
    assert decision.observed_confidence <= decision.baseline_confidence


def test_ood_input_cannot_strengthen_or_be_accepted() -> None:
    with pytest.raises(ValidationError):
        OODDecision(
            input_id="camera-frame-18", baseline_confidence=0.3, observed_confidence=0.9,
            out_of_distribution=True, disposition=OODDisposition.DEGRADED, coverage="degraded",
        )
    with pytest.raises(ValidationError):
        OODDecision(
            input_id="camera-frame-19", baseline_confidence=0.8, observed_confidence=0.8,
            out_of_distribution=True, disposition=OODDisposition.ACCEPT, coverage="sufficient",
        )
