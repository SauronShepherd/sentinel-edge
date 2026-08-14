from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario


def test_simultaneous_event_scenario_is_deterministic_and_prioritizes_seismic() -> None:
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    first = DeterministicScenarioEngine().run(scenario)
    second = DeterministicScenarioEngine().run(scenario)
    assert first.final_states == second.final_states
    assert first.dispatch_order == second.dispatch_order
    assert first.schedule_digest == second.schedule_digest
    assert first.trace_ids == second.trace_ids
    assert first.timing_metrics == second.timing_metrics
    assert all({"capture_at", "ingest_at", "release_at", "decision_at", "acquisition_delay_ms", "queue_age_ms"} <= set(row) for row in first.timing_metrics.values())
    assert all(row["acquisition_delay_ms"] >= 0 and row["queue_age_ms"] >= 0 for row in first.timing_metrics.values())
    assert all({"event_time", "ingest_time", "decision_time", "event_to_ingest_ms", "ingest_to_decision_ms", "event_to_decision_ms"} <= set(row) for row in first.latency_report.values())
    assert first.dispatch_order[0] == "earthquake-trigger"
    assert set(first.final_states) == {"wildfire", "flood", "earthquake", "landslide"}
    assert first.opportunity_balanced is True
    assert first.opportunity_counts["processed"] == 4
