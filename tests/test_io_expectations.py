from sentinel_edge.qualification.io_expectations import IoWorkloadExpectation


def test_io_workload_registry_declares_bounded_expectations() -> None:
    record = IoWorkloadExpectation("critical-evidence", "wal-evidence", "critical", 1000, 2000, True, 4096, "full").registry_record()
    assert record["write_bytes_limit"] == 2000
    assert record["fsync_required"] is True
    assert record["temporary_space_bytes_limit"] == 4096
