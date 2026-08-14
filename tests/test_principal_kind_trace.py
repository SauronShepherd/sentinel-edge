from datetime import datetime, timedelta, timezone

from sentinel_edge.domain.models import AuthorizationDecision, PrincipalRef, PrincipalRole


def test_authorization_trace_preserves_explicit_principal_kind_and_auth_method():
    principal = PrincipalRef(principal_id="sensor-service", roles=(PrincipalRole.OPERATOR,), authentication_method="mTLS", principal_kind="service")
    accepted = datetime.now(timezone.utc)
    decision = AuthorizationDecision(principal=principal, operation="observe", target="collector", payload_sha256="a" * 64, policy_version="auth-v1", accepted_at=accepted, expires_at=accepted + timedelta(seconds=1), authorization_tag="tag")
    assert decision.principal.principal_kind == "service"
    assert decision.principal.authentication_method == "mTLS"
