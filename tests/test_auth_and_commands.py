from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from sentinel_edge.domain.models import (
    AuthorizedReviewCommand,
    HazardKind,
    PrincipalRef,
    PrincipalRole,
    ReviewActionKind,
)
from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.security import AuthorizationError


def test_roles_public_schema_and_principal_self_assertion_are_enforced(
    viewer_headers: dict[str, str], operator_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    assert client.post("/v1/scenarios/run", json=scenario, headers=viewer_headers).status_code == 403
    assert client.post("/v1/scenarios/run", json=scenario, headers=operator_headers).status_code == 200

    forged = client.post(
        "/v1/incidents/earthquake/acknowledge",
        json={"idempotency_key": "forged-1", "actor": "admin", "roles": ["admin"]},
        headers=operator_headers,
    )
    assert forged.status_code == 422

    schema = client.get("/openapi.json").json()
    acknowledge = schema["components"]["schemas"]["ClientAcknowledgeRequest"]
    assert set(acknowledge["properties"]) == {"idempotency_key"}
    serialized = str(acknowledge).lower()
    assert "actor" not in serialized and "principal" not in serialized and "role" not in serialized


def test_principal_scoped_idempotency_and_payload_conflict(
    operator_headers: dict[str, str], admin_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    assert client.post("/v1/scenarios/run", json=scenario, headers=operator_headers).status_code == 200

    first = client.post(
        "/v1/incidents/earthquake/acknowledge",
        json={"idempotency_key": "same-client-key"},
        headers=operator_headers,
    )
    replay = client.post(
        "/v1/incidents/earthquake/acknowledge",
        json={"idempotency_key": "same-client-key"},
        headers=operator_headers,
    )
    assert first.status_code == 200 and replay.status_code == 200
    assert first.json()["receipt"]["command_id"] == replay.json()["receipt"]["command_id"]
    assert replay.json()["state"]["review_count"] == 1

    # The same client key under another principal is a different idempotency scope.
    other_principal = client.post(
        "/v1/incidents/earthquake/acknowledge",
        json={"idempotency_key": "same-client-key"},
        headers=admin_headers,
    )
    assert other_principal.status_code == 200
    assert other_principal.json()["receipt"]["command_id"] != first.json()["receipt"]["command_id"]
    assert other_principal.json()["state"]["review_count"] == 2

    until_a = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
    until_b = (datetime.now(timezone.utc) + timedelta(minutes=40)).isoformat()
    snooze = client.post(
        "/v1/incidents/flood/snooze",
        json={"idempotency_key": "snooze-conflict", "until": until_a},
        headers=operator_headers,
    )
    conflict = client.post(
        "/v1/incidents/flood/snooze",
        json={"idempotency_key": "snooze-conflict", "until": until_b},
        headers=operator_headers,
    )
    assert snooze.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "command_conflict"


def test_component4_rejects_payload_substitution_and_expired_authority() -> None:
    engine = DeterministicScenarioEngine()
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    current = next(item for item in engine.incidents.current() if item.hazard is HazardKind.EARTHQUAKE)
    principal = PrincipalRef(principal_id="operator-x", roles=(PrincipalRole.OPERATOR,))
    accepted = datetime.now(timezone.utc)
    payload = {
        "incident_id": str(current.incident_id),
        "hazard": HazardKind.EARTHQUAKE.value,
        "action": ReviewActionKind.ACKNOWLEDGE.value,
        "snooze_until": None,
        "comment": None,
        "idempotency_key": "tamper-1",
    }
    decision = engine.incidents.command_authorizer.decide(
        principal,
        operation="incidents:acknowledge",
        target=f"incident:{current.incident_id}",
        payload=payload,
        accepted_at=accepted,
    )
    tampered = AuthorizedReviewCommand(
        incident_id=current.incident_id,
        hazard=HazardKind.EARTHQUAKE,
        action=ReviewActionKind.SNOOZE,
        snooze_until=accepted + timedelta(minutes=5),
        idempotency_key="tamper-1",
        authorization=decision,
        payload_sha256=decision.payload_sha256,
        submitted_at=accepted,
    )
    with pytest.raises(AuthorizationError, match="operation or target mismatch|payload mismatch"):
        engine.incidents.apply_authorized_review(tampered)

    expired_decision = decision.model_copy(
        update={
            "accepted_at": accepted - timedelta(minutes=2),
            "expires_at": accepted - timedelta(minutes=1),
        }
    )
    expired = AuthorizedReviewCommand(
        incident_id=current.incident_id,
        hazard=HazardKind.EARTHQUAKE,
        action=ReviewActionKind.ACKNOWLEDGE,
        idempotency_key="expired-1",
        authorization=expired_decision,
        payload_sha256=expired_decision.payload_sha256,
        submitted_at=accepted,
    )
    with pytest.raises(AuthorizationError, match="expired"):
        engine.incidents.apply_authorized_review(expired)


def test_generated_bearer_tokens_are_csprng_and_not_time_derived() -> None:
    from sentinel_edge.security import generate_bearer_token

    tokens = {generate_bearer_token() for _ in range(128)}
    assert len(tokens) == 128
    assert min(len(token) for token in tokens) >= 43


def test_authorization_canonical_encoding_version_is_pinned(operator_headers: dict[str, str]) -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import PrincipalRef, PrincipalRole
    from sentinel_edge.security import AuthorizationError, CommandAuthorizer

    authorizer = CommandAuthorizer.development()
    principal = PrincipalRef(principal_id="operator", roles=(PrincipalRole.OPERATOR,))
    payload = {"action": "acknowledge"}
    decision = authorizer.decide(principal, operation="incidents:acknowledge", target="incident:1", payload=payload)
    incompatible = decision.model_copy(update={"canonical_encoding_version": "sentinel-cjson-v2"})
    with pytest.raises(AuthorizationError, match="canonical encoding version"):
        authorizer.verify(
            incompatible,
            payload=payload,
            operation="incidents:acknowledge",
            target="incident:1",
            current_principal=principal,
            now=decision.accepted_at,
        )
