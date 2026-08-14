from sentinel_edge.projections.service import ProjectionClientBuffer


def test_slow_client_overflow_is_bounded_and_requires_resync():
    buffer = ProjectionClientBuffer(capacity=2)
    assert buffer.offer("p1") == "queued"
    assert buffer.offer("p2") == "queued"
    assert buffer.offer("p3") == "resync_required"
    assert buffer.resync_required is True
    assert buffer.drain() == ()
    assert buffer.offer("p4") == "resync_required"
    buffer.reset_after_resync()
    assert buffer.offer("p5") == "queued"
    assert buffer.drain() == ("p5",)


def test_client_buffer_never_exceeds_configured_capacity():
    buffer = ProjectionClientBuffer(capacity=3)
    for item in ("p1", "p2", "p3"):
        assert buffer.offer(item) == "queued"
    assert len(buffer._items) == 3
