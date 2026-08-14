import pytest

from sentinel_edge.collector import evaluate_external_trigger, measure_trigger_path


def test_external_trigger_is_deterministic_and_bounded() -> None:
    quiet = [(0.1, 0.0, 0.0)] * 32
    event = quiet[:16] + [(2.0, 0.0, 0.0)] + quiet[17:]
    assert evaluate_external_trigger(quiet).reason == "below_threshold"
    assert evaluate_external_trigger(event).reason == "threshold_crossed"
    measurement = measure_trigger_path(event, repetitions=25)
    assert measurement.deterministic is True
    assert measurement.triggered_count == 25
    assert measurement.sample_count == 32
    assert measurement.worst_elapsed_ns >= 0


def test_external_trigger_has_no_dependency_on_linux_load_or_model_runtime() -> None:
    samples = [(0.0, 0.0, 0.0), (1.6, 0.0, 0.0)]
    baseline = evaluate_external_trigger(samples)
    # Extra unrelated work does not alter the pure decision path.
    _ = sum(index * index for index in range(10_000))
    assert evaluate_external_trigger(samples) == baseline


def test_external_trigger_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        evaluate_external_trigger([], threshold=-1.0)
    with pytest.raises(ValueError):
        measure_trigger_path([], repetitions=0)
