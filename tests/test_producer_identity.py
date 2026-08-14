from sentinel_edge.domain.models import PrincipalRef, PrincipalRole
from sentinel_edge.security.auth import authorize_producer_identity


def test_service_principal_subject_mismatch_is_denied_with_audit_reason():
    principal = PrincipalRef(principal_id="component-a", principal_kind="service", roles=(PrincipalRole.OPERATOR,))
    decision = authorize_producer_identity(principal, sending_component="component-b")
    assert decision.allowed is False
    assert decision.reason == "producer_identity_mismatch_audited"


def test_matching_machine_identity_is_allowed_and_humans_remain_role_governed():
    service = PrincipalRef(principal_id="component-a", principal_kind="service", roles=(PrincipalRole.OPERATOR,))
    human = PrincipalRef(principal_id="operator", roles=(PrincipalRole.OPERATOR,))
    assert authorize_producer_identity(service, sending_component="component-a").allowed is True
    assert authorize_producer_identity(human, sending_component="other-component").allowed is True
