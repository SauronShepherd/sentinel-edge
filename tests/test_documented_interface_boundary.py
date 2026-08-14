from sentinel_edge.collector import reject_page_scrape


def test_unstable_html_page_scraping_is_rejected() -> None:
    result = reject_page_scrape("<html><body>dynamic portal</body></html>", content_type="text/html")
    assert result.state == "rejected"
    assert result.resolution_permitted is False
    assert "unstable_page_scraping_not_permitted" in result.reason_codes


def test_non_html_reference_remains_reference_only_until_documented_adapter() -> None:
    result = reject_page_scrape("https://example.invalid/document.json", content_type="application/json")
    assert result.state == "reference_only"
    assert result.resolution_permitted is False
