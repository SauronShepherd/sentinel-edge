import pytest

from sentinel_edge.qualification.assumption_log import AssumptionLog, AssumptionRecord


def record(sequence: int, assumption_id: str, resolved: bool = False) -> AssumptionRecord:
    return AssumptionRecord(
        sequence=sequence,
        assumption_id=assumption_id,
        hazard_id="hazard-monitoring-gap",
        statement="Target host clock quality is measured before field qualification.",
        owner="qualification",
        resolved=resolved,
    )


def test_assumption_log_is_append_only_and_judge_visible() -> None:
    log = AssumptionLog().append(record(1, "A-001")).append(record(2, "A-002", resolved=True))
    assert [item["assumption_id"] for item in log.unresolved_for_judge_proof()] == ["A-001"]
    assert log.records[0].sequence == 1


def test_assumption_log_rejects_gaps_and_rewrites() -> None:
    log = AssumptionLog().append(record(1, "A-001"))
    with pytest.raises(ValueError):
        log.append(record(3, "A-003"))
    with pytest.raises(ValueError):
        log.append(record(2, "A-001"))
