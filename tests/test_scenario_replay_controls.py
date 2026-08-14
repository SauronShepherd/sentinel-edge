from sentinel_edge.scenario import ReplayMode, compare_replays, load_scenario, replay_scenario


def test_reset_accelerated_and_step_through_replays_have_identical_emissions() -> None:
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    runs = tuple(replay_scenario(scenario, mode=mode) for mode in ReplayMode)
    comparison = compare_replays(*runs)
    assert comparison.passed is True
    assert len(set(comparison.emission_sha256)) == 1
    assert len(set(comparison.release_orders)) == 1
    assert runs[-1].step_count == len(scenario["observations"])


def test_replay_comparison_detects_changed_release_order() -> None:
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    first = replay_scenario(scenario)
    altered = first.model_copy(update={"result": first.result.model_copy(update={"dispatch_order": tuple(reversed(first.result.dispatch_order))})})
    comparison = compare_replays(first, altered)
    assert comparison.passed is False
    assert comparison.mismatch_paths == ("run[1].emission",)
