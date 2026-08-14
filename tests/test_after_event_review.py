from copy import deepcopy

from sentinel_edge.review import AfterEventReviewBuilder
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.storage import ContentAddressedArtifactStore


def test_after_event_review_is_deterministic_complete_and_hash_verified(tmp_path) -> None:
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    first_engine = DeterministicScenarioEngine()
    second_engine = DeterministicScenarioEngine()
    first_result = first_engine.run(scenario)
    second_result = second_engine.run(scenario)
    builder = AfterEventReviewBuilder()
    first = builder.build(first_engine, first_result)
    second = builder.build(second_engine, second_result)

    assert first == second
    assert builder.verify(first)
    assert first["generation_policy"] == "deterministic_structured_evidence_only"
    assert "coverage_gaps" in first
    assert "delays_and_service_misses" in first
    assert first["false_alarms"]["assessment_state"] == "not_assessed_without_ground_truth"
    assert first["misses"]["assessment_state"] == "not_assessed_without_ground_truth"
    assert first["unresolved_actions"]

    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    ref = builder.write(first_engine, first_result, store)
    assert store.verify(ref)

    tampered = deepcopy(first)
    tampered["summary"]["observations"] += 1
    assert builder.verify(tampered) is False
