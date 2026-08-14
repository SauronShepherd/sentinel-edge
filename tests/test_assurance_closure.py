from sentinel_edge.qualification.assurance_case import ClosureState, evaluate_closure


def test_closure_rejects_unsupported_close():
    decision = evaluate_closure()
    assert decision.state is ClosureState.OPEN
    assert decision.reason == "closure_requires_evidence_or_accepted_debt"


def test_closure_accepts_evidence_or_explicit_debt():
    assert evaluate_closure(evidence_ids=("receipt:1",)).state is ClosureState.CLOSED
    debt = evaluate_closure(accepted_debt_id="debt:1")
    assert debt.state is ClosureState.CLOSED
    assert debt.accepted_debt_id == "debt:1"
