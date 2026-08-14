import pytest

from sentinel_edge.release.generation_policy import ExecutionPath, generated_prose_allowed, require_deterministic_wording


def test_generated_prose_is_disabled_on_authoritative_paths() -> None:
    for path in (ExecutionPath.CRITICAL_STATE, ExecutionPath.JUDGE, ExecutionPath.BENCHMARK):
        assert generated_prose_allowed(path) is False
        with pytest.raises(PermissionError):
            require_deterministic_wording(path, generated=True)


def test_operator_review_may_use_optional_generated_prose() -> None:
    assert generated_prose_allowed(ExecutionPath.OPERATOR_REVIEW) is True
    require_deterministic_wording(ExecutionPath.OPERATOR_REVIEW, generated=True)
