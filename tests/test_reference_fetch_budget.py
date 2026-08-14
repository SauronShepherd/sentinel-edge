import pytest

from sentinel_edge.collector.references import ReferenceFetchBudget, validate_fetch_result


def test_reference_fetch_budget_accepts_bounded_document() -> None:
    result = validate_fetch_result(
        url="https://example.com/feed", redirect_count=1, port=443,
        compressed_bytes=100, decompressed_bytes=500, mime_type="application/json",
        elapsed_ms=200,
    )
    assert result.reason_codes == ("fetch_budget_validated",)


def test_reference_fetch_budget_rejects_resource_fuzz_overages() -> None:
    result = validate_fetch_result(
        url="https://example.com/feed", redirect_count=4, port=8080,
        compressed_bytes=6_000_000, decompressed_bytes=21_000_000,
        mime_type="text/html", elapsed_ms=11_000,
    )
    assert result.state == "rejected"
    assert {"redirect_budget_exceeded", "port_not_allowlisted", "mime_type_not_allowlisted", "wall_time_budget_exceeded"} <= set(result.reason_codes)


def test_reference_budget_rejects_invalid_limits() -> None:
    with pytest.raises(ValueError):
        ReferenceFetchBudget(max_bytes=10, max_decompressed_bytes=5)
