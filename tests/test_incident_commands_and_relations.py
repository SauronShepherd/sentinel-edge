from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from datetime import datetime, timezone
from uuid import uuid4

from sentinel_edge.domain.models import AnalysisResult, CommandStatus, CoverageState, HazardKind, IncidentCommandKind, IncidentState, IncidentStatusCommand, validate_command_status_transition
from sentinel_edge.incidents import IncidentEventEngine
from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import load_scenario


def seeded_client(operator_headers: dict[str, str]) -> TestClient:
    client = TestClient(create_app())
    response = client.post(
        "/v1/scenarios/run",
        json=load_scenario("fixtures/scenarios/simultaneous-event.json"),
        headers=operator_headers,
    )
    assert response.status_code == 200
    return client


def test_out_of_order_analysis_preserves_newer_incident_version() -> None:
    engine = IncidentEventEngine()
    newer_time = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    newer = AnalysisResult(observation_id=uuid4(), hazard=HazardKind.EARTHQUAKE, score=0.9,
                           state_hint=IncidentState.CONFIRMED, features={}, coverage=CoverageState.SUFFICIENT,
                           event_time=newer_time)
    older = AnalysisResult(observation_id=uuid4(), hazard=HazardKind.EARTHQUAKE, score=0.1,
                           state_hint=IncidentState.SUSPECTED, features={}, coverage=CoverageState.SUFFICIENT,
                           event_time=datetime(2026, 8, 12, 9, 59, tzinfo=timezone.utc))
    committed = engine.apply_analysis(newer, accepted_at=newer_time)
    replay = engine.apply_analysis(older, accepted_at=newer_time)
    assert replay == committed
    assert replay.version == 1
    assert replay.event_time_watermark == newer_time


def test_unreviewed_confirmed_incident_cannot_be_resolved() -> None:
    engine = IncidentEventEngine()
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    incident = engine.apply_analysis(AnalysisResult(
        observation_id=uuid4(), hazard=HazardKind.WILDFIRE, score=0.95,
        state_hint=IncidentState.CONFIRMED, features={}, coverage=CoverageState.SUFFICIENT,
        produced_at=now,
    ), accepted_at=now)
    with pytest.raises(ValueError, match="unreviewed high-severity incident"):
        engine.apply_status_command(IncidentStatusCommand(
            incident_id=incident.incident_id, hazard=HazardKind.WILDFIRE,
            command=IncidentCommandKind.RESOLVE,
            expected_version=incident.version, actor="admin", reason="auto close", idempotency_key="auto-close-1", submitted_at=now,
        ))


def test_blind_required_sensor_cannot_resolve_event() -> None:
    engine = IncidentEventEngine()
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    incident = engine.apply_analysis(AnalysisResult(
        observation_id=uuid4(), hazard=HazardKind.WILDFIRE, score=0.7,
        state_hint=IncidentState.CONFIRMED, features={}, coverage=CoverageState.SUFFICIENT,
        produced_at=now,
    ), accepted_at=now)
    engine._current[HazardKind.WILDFIRE] = incident.model_copy(update={"state": IncidentState.RESOLVING, "coverage": CoverageState.BLIND})
    with pytest.raises(ValueError, match="blind required sensor cannot resolve"):
        engine.apply_status_command(IncidentStatusCommand(
            incident_id=incident.incident_id, hazard=HazardKind.WILDFIRE,
            command=IncidentCommandKind.RESOLVE, expected_version=incident.version,
            actor="admin", reason="resolve", idempotency_key="blind-resolve-1", submitted_at=now,
        ))


def test_command_lifecycle_is_distinct_from_projection_state() -> None:
    assert validate_command_status_transition(CommandStatus.ACCEPTED, CommandStatus.VALIDATING) is CommandStatus.VALIDATING
    assert validate_command_status_transition(CommandStatus.COMMITTED, CommandStatus.PROJECTED) is CommandStatus.PROJECTED
    with pytest.raises(ValueError, match="illegal command lifecycle transition"):
        validate_command_status_transition(CommandStatus.PROJECTED, CommandStatus.COMMITTED)


def current_by_hazard(client: TestClient, headers: dict[str, str]) -> dict[str, dict]:
    return {item["hazard"]: item for item in client.get("/v1/incidents", headers=headers).json()}


def test_incident_commands_are_version_checked_idempotent_and_high_impact_scoped(
    operator_headers: dict[str, str], admin_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = seeded_client(operator_headers)
    current = current_by_hazard(client, viewer_headers)["wildfire"]
    corroborate = {
        "command": "corroborate",
        "expected_version": current["version"],
        "reason": "second independent local observation",
        "idempotency_key": "wildfire-corroborate-1",
    }
    first = client.post("/v1/incidents/wildfire/commands", json=corroborate, headers=operator_headers)
    assert first.status_code == 200
    assert first.json()["version"] == current["version"] + 1
    assert first.json()["command_lifecycle"] == "committed"
    assert first.json()["projection_state"] == "projected"
    assert first.json()["projection"]["schema"] == "sentinel-edge-incident-projection/1.0"
    retry = client.post("/v1/incidents/wildfire/commands", json=corroborate, headers=operator_headers)
    assert retry.status_code == 200
    assert retry.json()["version"] == first.json()["version"]

    stale = client.post(
        "/v1/incidents/wildfire/commands",
        json={**corroborate, "idempotency_key": "stale", "reason": "stale", "expected_version": current["version"]},
        headers=operator_headers,
    )
    assert stale.status_code == 409
    assert "reconfirmation" in stale.json()["detail"]["message"]

    stale_resolve = client.post(
        "/v1/incidents/wildfire/commands",
        json={
            "command": "resolve",
            "expected_version": current["version"],
            "reason": "stale high-impact decision",
            "idempotency_key": "resolve-stale",
        },
        headers=admin_headers,
    )
    assert stale_resolve.status_code == 409
    assert "reconfirmation" in stale_resolve.json()["detail"]["message"]
    # The rejected concurrent loser must not append a second lifecycle event.
    assert stale.json()["detail"]["code"] == "incident_command_conflict"

    denied = client.post(
        "/v1/incidents/wildfire/commands",
        json={
            "command": "resolve",
            "expected_version": first.json()["version"],
            "reason": "operator believes event ended",
            "idempotency_key": "resolve-denied",
        },
        headers=operator_headers,
    )
    assert denied.status_code == 403

    resolving = client.post(
        "/v1/incidents/wildfire/commands",
        json={
            "command": "resolve",
            "expected_version": first.json()["version"],
            "reason": "admin reviewed negative local evidence",
            "idempotency_key": "resolve-1",
        },
        headers=admin_headers,
    )
    assert resolving.status_code == 200
    assert resolving.json()["state"] == "resolving"
    resolved = client.post(
        "/v1/incidents/wildfire/commands",
        json={
            "command": "resolve",
            "expected_version": resolving.json()["version"],
            "reason": "resolution window completed",
            "idempotency_key": "resolve-2",
        },
        headers=admin_headers,
    )
    assert resolved.status_code == 200
    assert resolved.json()["state"] == "resolved"
    reopened = client.post(
        "/v1/incidents/wildfire/commands",
        json={
            "command": "reopen",
            "expected_version": resolved.json()["version"],
            "reason": "new local evidence",
            "idempotency_key": "reopen-1",
        },
        headers=admin_headers,
    )
    assert reopened.status_code == 200
    assert reopened.json()["state"] == "suspected"


def test_cross_hazard_link_preserves_separate_incidents(
    operator_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = seeded_client(operator_headers)
    incidents = current_by_hazard(client, viewer_headers)
    wildfire = incidents["wildfire"]
    landslide = incidents["landslide"]
    response = client.post(
        "/v1/incidents/wildfire/commands",
        json={
            "command": "link",
            "expected_version": wildfire["version"],
            "reason": "post-fire slope susceptibility context",
            "related_incident_id": landslide["incident_id"],
            "related_hazard": "landslide",
            "idempotency_key": "wf-landslide-link-1",
        },
        headers=operator_headers,
    )
    assert response.status_code == 200
    assert response.json()["relation"] == "temporal_association"
    relations = client.get("/v1/incidents/relations", headers=viewer_headers).json()
    assert len(relations) == 1
    after = current_by_hazard(client, viewer_headers)
    assert after["wildfire"]["incident_id"] == wildfire["incident_id"]
    assert after["landslide"]["incident_id"] == landslide["incident_id"]


def test_same_hazard_merge_creates_alias_relation_without_deleting_history() -> None:
    from datetime import datetime, timezone
    from uuid import uuid4

    from sentinel_edge.domain.models import (
        CoverageState,
        HazardKind,
        IncidentCommandKind,
        IncidentRecord,
        IncidentState,
        IncidentStatusCommand,
)
    from sentinel_edge.incidents import IncidentEventEngine
    from sentinel_edge.storage import IncidentJournalStore

    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    store = IncidentJournalStore()
    older = IncidentRecord(
        incident_id=uuid4(), hazard=HazardKind.WILDFIRE, state=IncidentState.RESOLVED,
        confidence=0.4, coverage=CoverageState.SUFFICIENT, first_observed_at=now,
        last_observed_at=now, version=1,
    )
    newer = IncidentRecord(
        incident_id=uuid4(), hazard=HazardKind.WILDFIRE, state=IncidentState.SUSPECTED,
        confidence=0.8, coverage=CoverageState.SUFFICIENT, first_observed_at=now,
        last_observed_at=now, version=2,
    )
    store.append(older)
    store.append(newer)
    engine = IncidentEventEngine(store)
    relation = engine.apply_status_command(IncidentStatusCommand(
        incident_id=newer.incident_id,
        hazard=HazardKind.WILDFIRE,
        command=IncidentCommandKind.MERGE,
        expected_version=2,
        actor="admin",
        reason="same incident after temporal-spatial review",
        related_incident_id=older.incident_id,
        related_hazard=HazardKind.WILDFIRE,
        idempotency_key="merge-wildfire-1",
    ))
    assert relation.relation.value == "merged_alias"
    assert len(store.all()) == 2
    assert {item.incident_id for item in store.all()} == {older.incident_id, newer.incident_id}


def test_contradiction_update_is_versioned_without_erasing_incident(
    operator_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = seeded_client(operator_headers)
    current = current_by_hazard(client, viewer_headers)["earthquake"]
    response = client.post(
        "/v1/incidents/earthquake/commands",
        json={
            "command": "contradict",
            "expected_version": current["version"],
            "reason": "peer waveform does not corroborate local trigger",
            "idempotency_key": "eq-contradict-1",
        },
        headers=operator_headers,
    )
    assert response.status_code == 200
    assert response.json()["version"] == current["version"] + 1
    assert response.json()["incident_id"] == current["incident_id"]
    assert response.json()["confidence"] < current["confidence"]
    assert any(code == "operator_contradict" for code in response.json()["reason_codes"])
