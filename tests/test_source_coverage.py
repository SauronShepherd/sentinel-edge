import pytest
from pydantic import ValidationError

from sentinel_edge.integrations.coverage import SourceCoverage


def test_source_coverage_exposes_missing_contributor_and_page() -> None:
    coverage = SourceCoverage(
        source_id="federated-feed", expected_spatial=2, received_spatial=2,
        expected_temporal=4, received_temporal=4, expected_pages=3, received_pages=2,
        expected_contributors=2, received_contributors=1,
    )
    assert coverage.missing_dimensions() == ("pages", "tiles", "contributors")


def test_source_coverage_rejects_impossible_received_counts() -> None:
    with pytest.raises(ValidationError):
        SourceCoverage(source_id="feed", expected_tiles=1, received_tiles=2)
