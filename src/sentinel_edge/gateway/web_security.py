"""Fail-closed web boundary policy helpers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WebSecurityPolicy:
    allowed_hosts: frozenset[str] = frozenset({"localhost", "127.0.0.1", "testserver"})
    trusted_proxies: frozenset[str] = frozenset()
    allowed_origins: frozenset[str] = frozenset()
    allow_bearer_plaintext: bool = False

    def host_allowed(self, host: str) -> bool:
        return host.split(":", 1)[0].lower() in self.allowed_hosts

    def forwarded_headers(self, *, peer_host: str, headers: dict[str, str]) -> dict[str, str]:
        if peer_host not in self.trusted_proxies:
            return {}
        return {key: value for key, value in headers.items() if key.lower() in {"forwarded", "x-forwarded-for", "x-forwarded-proto", "x-forwarded-host"}}

    def origin_allowed(self, origin: str | None) -> bool:
        return origin is not None and origin in self.allowed_origins

    def browser_write_allowed(self, *, origin: str | None, csrf_token: str | None) -> bool:
        return self.origin_allowed(origin) and bool(csrf_token and csrf_token.strip())

    def websocket_upgrade_allowed(self, *, origin: str | None, authenticated: bool) -> bool:
        """Authorize projection-only upgrades; never a mutation channel."""
        return authenticated and self.origin_allowed(origin)

    def bearer_transport_allowed(self, *, scheme: str, host: str) -> bool:
        return scheme.lower() == "https" or (host.split(":", 1)[0] in {"localhost", "127.0.0.1", "testserver"} and self.allow_bearer_plaintext)
