from __future__ import annotations

import pytest

from sentinel_edge.collector import BoundedBackgroundConnector, ConnectorMode, validate_reference, validate_resolved_addresses
from sentinel_edge.domain.models import SourceMode


def test_submitted_url_is_reference_only_by_default() -> None:
    decision = validate_reference("HTTPS://Example.COM/path#ignored")
    assert decision.state == "rejected"
    assert decision.resolution_permitted is False


def test_explicit_allowlist_is_required_for_resolution() -> None:
    not_allowed = validate_reference("https://example.com/path", permit_resolution=True)
    assert not_allowed.state == "reference_only"
    allowed = validate_reference(
        "HTTPS://Example.COM/path", permit_resolution=True, allowed_hosts=frozenset({"example.com"})
    )
    assert allowed.state == "resolution_permitted"
    assert allowed.canonical_url == "https://example.com/path"


def test_local_and_ambiguous_targets_fail_closed() -> None:
    for value in (
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://localhost/",
        "file:///etc/passwd",
        "https://user:password@example.com/",
    ):
        assert validate_reference(value).state == "rejected"


def test_dns_name_is_not_treated_as_proof_of_public_reachability() -> None:
    decision = validate_reference("https://example.com", permit_resolution=True, allowed_hosts=frozenset({"example.com"}))
    assert decision.resolution_permitted is True
    assert "explicit_policy_and_allowlist" in decision.reason_codes


def test_resolved_addresses_are_revalidated_before_connect() -> None:
    assert validate_resolved_addresses(("93.184.216.34", "2001:4860:4860::8888")) == (
        "2001:4860:4860::8888",
        "93.184.216.34",
    )
    with pytest.raises(ValueError, match="local or reserved"):
        validate_resolved_addresses(("93.184.216.34", "10.0.0.1"))
    with pytest.raises(ValueError, match="no addresses"):
        validate_resolved_addresses(())


def test_connector_reference_submission_cannot_bypass_source_policy() -> None:
    received: list[str] = []
    connector = BoundedBackgroundConnector("live", received.append, source_mode=SourceMode.LIVE, connector_mode=ConnectorMode.POLL, allowed_hosts=frozenset({"example.com"}))
    connector.start()
    with pytest.raises(ValueError, match="local or reserved"):
        connector.submit_reference("https://127.0.0.1/")
    connector.submit_reference("https://example.com/feed")
    receipt = connector.drain_and_stop(deadline_seconds=1.0)
    assert receipt.processed_items == 1
    assert received == ["https://example.com/feed"]


def test_connector_transport_mode_is_explicit() -> None:
    connector = BoundedBackgroundConnector("fixture", lambda _: None, connector_mode=ConnectorMode.FIXTURE)
    assert connector.connector_mode is ConnectorMode.FIXTURE
    with pytest.raises(ValueError):
        ConnectorMode("arbitrary")


def test_connector_routes_submissions_through_component_one_normalizer() -> None:
    received: list[str] = []
    connector = BoundedBackgroundConnector("normalized", received.append, normalizer=lambda item: item.strip().lower())
    connector.start()
    connector.submit("  INPUT  ")
    connector.drain_and_stop(deadline_seconds=1.0)
    assert received == ["input"]
    rejected = BoundedBackgroundConnector("rejecting", lambda _: None, normalizer=lambda _: (_ for _ in ()).throw(ValueError("bad")))
    rejected.start()
    with pytest.raises(ValueError, match="normalization rejected"):
        rejected.submit("bad")
    rejected.drain_and_stop(deadline_seconds=1.0)
