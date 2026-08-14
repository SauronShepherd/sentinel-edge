import time

from sentinel_edge.runtime.acl_diagnostic import run_acl_diagnostic


def test_acl_diagnostic_is_time_bounded_and_never_blocks_release() -> None:
    result = run_acl_diagnostic(lambda: (time.sleep(0.05), "allow")[1], timeout_seconds=0.001)
    assert result.status == "timed_out"
    assert result.release_gate_blocked is False


def test_acl_diagnostic_returns_check_result_when_fast() -> None:
    result = run_acl_diagnostic(lambda: "deny", timeout_seconds=0.1)
    assert result.status == "deny"
    assert result.release_gate_blocked is False
