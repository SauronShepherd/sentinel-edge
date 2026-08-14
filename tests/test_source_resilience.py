from sentinel_edge.integrations.resilience import SourceCircuit


def test_source_outage_uses_bounded_backoff_cache_and_opens_circuit() -> None:
    circuit = SourceCircuit(failure_threshold=2, base_backoff_seconds=0.5)
    first = circuit.before_fetch(cache_available=True)
    assert first.allowed is True and first.use_cache is False and first.backoff_seconds == 0.0
    retry = circuit.record_failure(cache_available=True)
    assert retry.reason == "retry_backoff" and retry.use_cache is True and retry.backoff_seconds == 0.5
    opened = circuit.record_failure(cache_available=True)
    assert opened.reason == "circuit_open" and opened.allowed is False and opened.use_cache is True
    blocked = circuit.before_fetch(cache_available=False)
    assert blocked.allowed is False and blocked.use_cache is False and blocked.backoff_seconds == 1.0
    circuit.record_success()
    assert circuit.before_fetch(cache_available=False).allowed is True
