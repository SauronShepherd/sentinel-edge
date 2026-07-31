from sentinel_testkit import Scenario, VirtualClock

def test_clock_and_scenario_are_deterministic():
    first = Scenario("demo", [{"at": 1}], ["ordered"], seed=42)
    second = first.reset()
    assert first.semantic_hash() == second.semantic_hash()
    clock = VirtualClock(); assert clock.advance(2).isoformat() == "2026-01-01T00:00:02+00:00"
    first.record({"event": "x"})
    replay = first.reset(); replay.record({"event": "x"})
    assert [first.fault_choice(["a", "b"]) for _ in range(3)] == [replay.fault_choice(["a", "b"]) for _ in range(3)]
    assert first.semantic_hash() == replay.semantic_hash()

def test_different_seed_changes_seeded_fault_decision():
    first = Scenario("x", seed=1); second = Scenario("x", seed=2)
    assert [first.fault_choice(["a", "b"]) for _ in range(8)] != [second.fault_choice(["a", "b"]) for _ in range(8)]
