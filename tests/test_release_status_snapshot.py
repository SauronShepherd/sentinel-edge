import pytest

from sentinel_edge.release.status_snapshot import ReleaseStatusSnapshot


def test_release_status_publishes_count_delta_path_exceptions_and_budget() -> None:
    snapshot = ReleaseStatusSnapshot(10, 8, 2, ("target-host",), ("physical-evidence-open",), 3)
    assert snapshot.as_dict()["h0_delta"] == 2
    assert snapshot.as_dict()["optional_work_budget"] == 3


def test_release_status_rejects_inconsistent_delta_or_missing_path() -> None:
    with pytest.raises(ValueError, match="delta"):
        ReleaseStatusSnapshot(10, 8, 1, ("path",), (), 0)
    with pytest.raises(ValueError, match="critical path"):
        ReleaseStatusSnapshot(1, 1, 0, (), (), 0)
