import pytest

from sentinel_edge.qualification.delivery_matrix import CrashMatrixReport, CrashMatrixRow, CrashPoint


def test_crash_matrix_proves_one_effective_duplicate_mutation() -> None:
    report = CrashMatrixReport(message_contract="incident-command-v1", producer_outbox=True, consumer_inbox=True,
        rows=tuple(CrashMatrixRow(crash_point=point, delivery_attempts=2, effective_mutations=1,
            eventual_converged=True) for point in CrashPoint))
    assert len(report.rows) == 3
    assert all(row.effective_mutations == 1 for row in report.rows)


def test_crash_matrix_requires_all_points() -> None:
    with pytest.raises(ValueError):
        CrashMatrixReport(message_contract="x", producer_outbox=True, consumer_inbox=True,
            rows=(CrashMatrixRow(crash_point=CrashPoint.AFTER_ACK, delivery_attempts=1,
                effective_mutations=1, eventual_converged=True),))
