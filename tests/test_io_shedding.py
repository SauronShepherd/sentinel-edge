from sentinel_edge.runtime.io_shedding import decide_io_shedding


def test_io_pressure_sheds_optional_work_and_preserves_critical_truth() -> None:
    decision = decide_io_shedding(pressure_active=True)
    assert decision.critical_truth_preserved is True
    assert "previews" in decision.shed
    assert "garbage_collection" in decision.shed
    assert decision.degraded is True


def test_no_pressure_does_not_shed() -> None:
    assert decide_io_shedding(pressure_active=False).shed == ()
