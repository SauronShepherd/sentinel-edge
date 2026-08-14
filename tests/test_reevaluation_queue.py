import pytest

from sentinel_edge.review.reevaluation_queue import BoundedReevaluationQueue, ReevaluationItem, ReevaluationState


def test_queue_exposes_incomplete_and_failed_reevaluations() -> None:
    queue = BoundedReevaluationQueue(2)
    queue.enqueue(ReevaluationItem("a"))
    queue.enqueue(ReevaluationItem("b"))
    queue.finish("a", state=ReevaluationState.INCOMPLETE, reason="source_missing")
    queue.finish("b", state=ReevaluationState.FAILED, reason="worker_error")
    assert [item.state for item in queue.snapshot()] == [ReevaluationState.INCOMPLETE, ReevaluationState.FAILED]


def test_queue_is_bounded() -> None:
    queue = BoundedReevaluationQueue(1)
    queue.enqueue(ReevaluationItem("a"))
    with pytest.raises(OverflowError):
        queue.enqueue(ReevaluationItem("b"))
