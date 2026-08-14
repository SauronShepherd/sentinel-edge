from sentinel_edge.qualification.sources import validate_canonical_source_link


def test_canonical_source_link_requires_https_and_no_credentials_or_fragment() -> None:
    assert validate_canonical_source_link("https://example.com/docs/terms")[0] is True
    for url in ("http://example.com/docs", "https://user:pass@example.com/docs", "https://example.com/docs#part"):
        assert validate_canonical_source_link(url)[0] is False


def test_historical_reference_is_explicitly_non_current() -> None:
    valid, reasons = validate_canonical_source_link("https://example.com/archive", historical=True)
    assert valid is False
    assert "source_reference_historical_only" in reasons
