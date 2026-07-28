from sentinel_testkit import Scenario, VirtualClock

def test_clock_and_scenario_are_deterministic():
    first = Scenario("demo", [{"at": 1}], ["ordered"])
    second = first.reset()
    assert first.semantic_hash() == second.semantic_hash()
    clock = VirtualClock(); assert clock.advance(2).isoformat() == "2026-01-01T00:00:02+00:00"
