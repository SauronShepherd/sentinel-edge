from sentinel_edge.scenario import load_scenario
from sentinel_edge.scenario.replay import ReplayMode, replay_scenario


def test_replay_retains_what_was_known_at_each_decision_boundary() -> None:
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    run = replay_scenario(scenario, mode=ReplayMode.STEP_THROUGH)
    assert len(run.knowledge_snapshots) == len(scenario["observations"])
    assert run.knowledge_snapshots[0]["observation_id"] is None
    assert run.knowledge_snapshots[0]["known_values"] == scenario["observations"][0]["values"]
