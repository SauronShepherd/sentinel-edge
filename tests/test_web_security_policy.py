import pytest

from sentinel_edge.gateway.web_security import WebSecurityPolicy


def test_forwarded_headers_are_ignored_from_untrusted_peers() -> None:
    policy = WebSecurityPolicy(trusted_proxies=frozenset({"10.0.0.2"}))
    headers = {"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.5"}
    assert policy.forwarded_headers(peer_host="10.0.0.3", headers=headers) == {}
    assert policy.forwarded_headers(peer_host="10.0.0.2", headers=headers) == headers


def test_host_origin_csrf_and_bearer_transport_fail_closed() -> None:
    policy = WebSecurityPolicy(allowed_origins=frozenset({"https://localhost"}))
    assert policy.host_allowed("localhost:8000")
    assert not policy.host_allowed("evil.example")
    assert policy.browser_write_allowed(origin="https://localhost", csrf_token="csrf")
    assert not policy.browser_write_allowed(origin="https://evil.example", csrf_token="csrf")
    assert not policy.browser_write_allowed(origin="https://localhost", csrf_token=None)
    assert policy.bearer_transport_allowed(scheme="https", host="edge.example")
    assert not policy.bearer_transport_allowed(scheme="http", host="edge.example")


def test_browser_write_policy_requires_origin_and_csrf_together() -> None:
    policy = WebSecurityPolicy(allowed_origins=frozenset({"https://localhost"}))
    assert policy.browser_write_allowed(origin="https://localhost", csrf_token="csrf")
    assert not policy.browser_write_allowed(origin="https://localhost", csrf_token=None)


def test_websocket_upgrade_requires_allowed_origin_and_authentication() -> None:
    policy = WebSecurityPolicy(allowed_origins=frozenset({"https://localhost"}))
    assert policy.websocket_upgrade_allowed(origin="https://localhost", authenticated=True)
    assert not policy.websocket_upgrade_allowed(origin="https://evil.example", authenticated=True)
    assert not policy.websocket_upgrade_allowed(origin="https://localhost", authenticated=False)
