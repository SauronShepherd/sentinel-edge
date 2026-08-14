import pytest

from sentinel_edge.review.corrective_actions import ActionState, CorrectiveAction


def test_corrective_action_progression_records_audit_and_closure_evidence() -> None:
    action = CorrectiveAction("a1", "owner", "P1", "2026-09-01", "REQ-X", "TEST-X", ())
    action = action.advance(ActionState.VERIFIED, evidence="receipt-1")
    action = action.advance(ActionState.CLOSED, evidence="receipt-2")
    assert action.state is ActionState.CLOSED
    assert action.audit == ("open->verified:receipt-1", "verified->closed:receipt-2")


def test_closure_and_accepted_debt_require_evidence() -> None:
    action = CorrectiveAction("a1", "owner", "P1", "due", "REQ-X", "TEST-X", ())
    with pytest.raises(ValueError, match="closure evidence"):
        action.advance(ActionState.CLOSED)
    with pytest.raises(ValueError, match="accepted debt"):
        action.advance(ActionState.ACCEPTED_DEBT)
