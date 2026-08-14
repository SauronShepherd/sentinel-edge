from pathlib import Path

from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.storage import IncidentJournalStore


def test_authority_journal_has_contiguous_typed_digest_bound_subtypes(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    report = engine.incidents.authority_conformance()
    assert report["valid"] is True
    assert report["event_count"] == len(engine.incidents.authority_journal())
    assert report["highest_contiguous_position"] == report["event_count"]
    assert report["failures"] == ()


def test_authority_subtype_digest_corruption_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "incidents.sqlite3"
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    store = engine.incidents._store
    position = store.authority_journal()[0].position
    with store._connection:
        store._connection.execute(
            "UPDATE authority_event_subtypes SET payload_sha256='0' WHERE authority_position=?",
            (position,),
        )
    report = store.authority_conformance()
    assert report["valid"] is False
    assert any(item.startswith("subtype_digest_mismatch") for item in report["failures"])


def test_divergent_projection_is_detected_before_serving(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state-projection")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    assert engine.incidents.projection_conformance()["valid"] is True
    engine.incidents._current.pop(next(iter(engine.incidents._current)))
    report = engine.incidents.projection_conformance()
    assert report["valid"] is False
    assert "projection_hazard_set_mismatch" in report["failures"]
