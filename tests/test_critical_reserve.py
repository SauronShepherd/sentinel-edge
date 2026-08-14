from sentinel_edge.storage.critical_reserve import CriticalIoReserve


def test_optional_media_cannot_consume_critical_reserve() -> None:
    reserve = CriticalIoReserve(100, 64, 0.5)
    assert reserve.optional_write_allowed(free_bytes=120, write_bytes=30) is False
    assert reserve.optional_write_allowed(free_bytes=200, write_bytes=30) is True
    assert reserve.critical_write_allowed(write_bytes=64) is True
