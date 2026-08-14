from sentinel_edge.scenario import DeterministicScenarioEngine


def _record(engine, capability_id: str) -> dict:
    return next(item.model_dump(mode="json") for item in engine.capabilities.records() if item.capability_id == capability_id)


def test_distinct_module_faults_are_user_visible() -> None:
    engine = DeterministicScenarioEngine()
    engine.set_analysis_available(False, reason="analyzer_dependency_failed")
    assert _record(engine, "analysis")["reason_codes"] == ["analyzer_dependency_failed"]

    engine = DeterministicScenarioEngine()
    engine.set_runtime_available(False, reason="runtime_worker_failed")
    assert _record(engine, "runtime")["reason_codes"] == ["runtime_worker_failed"]

    engine = DeterministicScenarioEngine()
    engine.set_incident_authority_available(False, reason="incident_store_failed")
    assert _record(engine, "incident_authority")["reason_codes"] == ["critical_spool_active", "incident_store_failed"]

    engine = DeterministicScenarioEngine()
    engine.set_api_available(False, reason="api_dependency_failed")
    assert _record(engine, "api")["reason_codes"] == ["api_dependency_failed"]

    engine = DeterministicScenarioEngine()
    engine.set_storage_read_only()
    assert _record(engine, "evidence")["reason_codes"] == ["degraded_storage_read_only"]
