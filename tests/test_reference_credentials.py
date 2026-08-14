from sentinel_edge.collector.references import scrub_reference_headers


def test_reference_capture_never_forwards_private_credentials() -> None:
    headers = scrub_reference_headers({
        "Accept": "application/json", "Authorization": "Bearer operator-secret",
        "Cookie": "session=private", "X-Api-Key": "private-key", "X-Trace": "safe",
    })
    assert headers == {"Accept": "application/json", "X-Trace": "safe"}
