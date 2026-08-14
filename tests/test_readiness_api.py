from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_readiness_endpoint_exposes_explicit_barrier_state() -> None:
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "ready"
    assert body["checks"]["active_configuration"] is True
    assert body["checks"]["runtime_profiles_complete"] is True


def test_scenario_execution_is_fenced_when_readiness_is_blocked() -> None:
    from sentinel_edge.domain.models import ReadinessReport, ReadinessState, RuntimeMode
    from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario

    engine = DeterministicScenarioEngine()
    engine.readiness = ReadinessReport(
        state=ReadinessState.BLOCKED,
        mode=RuntimeMode.JUDGE,
        checks={"clock_usable": False},
        reason_codes=("clock_usable",),
    )
    try:
        engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    except RuntimeError as exc:
        assert "startup readiness barrier" in str(exc)
    else:
        raise AssertionError("blocked readiness must fence scenario execution")
