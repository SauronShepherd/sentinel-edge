import pytest
from pydantic import ValidationError

from sentinel_edge.qualification.assurance_case import AssuranceCase, AssuranceClaim


def test_assurance_case_requires_claim_hazard_control_test_and_residual_links() -> None:
    case = AssuranceCase(
        claims=(AssuranceClaim(
            claim_id="claim-watchdog-recovery",
            hazard_id="hazard-stale-monitoring",
            control_id="control-watchdog-recovery",
            test_ids=("TEST-WDG-001",),
            evidence_ids=("receipt:watchdog",),
            residual_limitation="Target-host recovery timing remains unqualified.",
        ),)
    )
    assert case.model_dump(mode="json")["claims"][0]["test_ids"] == ["TEST-WDG-001"]


def test_assurance_case_rejects_unlinked_claims() -> None:
    with pytest.raises(ValidationError):
        AssuranceClaim(
            claim_id="claim-incomplete",
            hazard_id="hazard-1",
            control_id="control-1",
            test_ids=(),
            evidence_ids=("receipt:1",),
            residual_limitation="limitation",
        )
