import pytest

from sentinel_edge.domain.models import PrincipalRef, PrincipalRole
from sentinel_edge.security import AuthManager, AuthorizationError


def test_non_human_principal_cannot_generate_operator_review():
    auth = AuthManager([("service-token-123456789", PrincipalRef(principal_id="model-worker", roles=(PrincipalRole.OPERATOR,), principal_kind="service"))])
    principal = auth.authenticate("service-token-123456789")
    with pytest.raises(AuthorizationError, match="non-human"):
        auth.authorize(principal, "reviews:generate")


def test_human_operator_retains_review_permission():
    auth = AuthManager([("operator-token-123456789", PrincipalRef(principal_id="operator", roles=(PrincipalRole.OPERATOR,), principal_kind="human"))])
    auth.authorize(auth.authenticate("operator-token-123456789"), "reviews:generate")
