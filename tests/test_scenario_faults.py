from datetime import datetime, timezone

from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
from sentinel_edge.scenario import DeterministicScenarioEngine, FaultKind, inject_fault, recover_fault


def seed_source(engine: DeterministicScenarioEngine) -> None:
    now = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    engine.collector.ingest(Observation(
        source_id="fault-source", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE,
        boot_id="fault-boot", sequence=1, observed_at=now, received_at=now,
        values={"accel_x": 0.1}, units={"accel_x": "g"},
    ))


def test_each_declared_fault_has_explicit_result_and_reversible_paths() -> None:
    engine = DeterministicScenarioEngine()
    try:
        seed_source(engine)
        for fault in FaultKind:
            result = inject_fault(engine, fault, source_id="fault-source")
            assert result.injected is True
            assert result.reason_code
        assert recover_fault(engine, FaultKind.STORAGE).recovered is True
        assert recover_fault(engine, FaultKind.WORKER).recovered is True
        assert recover_fault(engine, FaultKind.CLOCK).recovered is True
    finally:
        engine.close()


def test_source_fault_is_durable_and_requires_a_new_observation_to_recover() -> None:
    engine = DeterministicScenarioEngine()
    try:
        seed_source(engine)
        result = inject_fault(engine, FaultKind.SOURCE, source_id="fault-source")
        assert result.expected_state == "failed"
        recovery = recover_fault(engine, FaultKind.SOURCE, source_id="fault-source")
        assert recovery.recovered is False
        assert recovery.reason_code == "recovery_requires_new_observation"
    finally:
        engine.close()
