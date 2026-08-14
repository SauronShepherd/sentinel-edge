"""Fail-closed validation for externally submitted references.

This module deliberately does not fetch URLs.  A submitted URL is a reference
until a caller supplies an explicit resolution policy and an exact host
allowlist.  Network/DNS resolution remains an infrastructure concern and must
revalidate the destination immediately before connecting.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit
from collections.abc import Iterable


@dataclass(frozen=True)
class ReferenceDecision:
    """The deterministic outcome of URL admission."""

    canonical_url: str
    state: str
    resolution_permitted: bool
    reason_codes: tuple[str, ...]


_PRIVATE_REFERENCE_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization", "x-api-key", "x-auth-token"})


def scrub_reference_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return only safe reference headers; browser/operator credentials never cross the boundary."""
    return {key: value for key, value in headers.items() if key.lower() not in _PRIVATE_REFERENCE_HEADERS}


@dataclass(frozen=True)
class ReferenceFetchBudget:
    max_redirects: int = 3
    allowed_ports: frozenset[int] = frozenset({80, 443})
    max_bytes: int = 5 * 1024 * 1024
    max_decompressed_bytes: int = 20 * 1024 * 1024
    max_wall_time_ms: int = 10_000
    allowed_mime_types: frozenset[str] = frozenset({"application/json", "application/geo+json", "application/xml", "text/csv"})

    def __post_init__(self) -> None:
        if self.max_redirects < 0 or not self.allowed_ports or min(self.allowed_ports) < 1 or self.max_bytes <= 0 or self.max_decompressed_bytes < self.max_bytes or self.max_wall_time_ms <= 0 or not self.allowed_mime_types:
            raise ValueError("reference fetch budget is invalid")


def validate_fetch_result(*, url: str, redirect_count: int, port: int | None, compressed_bytes: int, decompressed_bytes: int, mime_type: str, elapsed_ms: int, budget: ReferenceFetchBudget = ReferenceFetchBudget()) -> ReferenceDecision:
    """Validate connector-reported resource usage without performing a fetch."""
    base = validate_reference(url)
    if base.state == "rejected":
        return base
    reasons: list[str] = []
    if redirect_count > budget.max_redirects: reasons.append("redirect_budget_exceeded")
    if port is not None and port not in budget.allowed_ports: reasons.append("port_not_allowlisted")
    if compressed_bytes < 0 or compressed_bytes > budget.max_bytes: reasons.append("compressed_byte_budget_exceeded")
    if decompressed_bytes < 0 or decompressed_bytes > budget.max_decompressed_bytes: reasons.append("decompressed_byte_budget_exceeded")
    if mime_type.split(";", 1)[0].strip().lower() not in budget.allowed_mime_types: reasons.append("mime_type_not_allowlisted")
    if elapsed_ms < 0 or elapsed_ms > budget.max_wall_time_ms: reasons.append("wall_time_budget_exceeded")
    return ReferenceDecision(base.canonical_url, "rejected" if reasons else "reference_only", False, tuple(reasons) or ("fetch_budget_validated",))


def reject_page_scrape(value: str, *, content_type: str | None = None) -> ReferenceDecision:
    """Keep HTML/page captures out of documented source-adapter paths."""
    if content_type and content_type.split(";", 1)[0].strip().lower() in {"text/html", "application/xhtml+xml"}:
        return ReferenceDecision(value, "rejected", False, ("unstable_page_scraping_not_permitted",))
    if value.lstrip().lower().startswith(("<!doctype html", "<html", "<head", "<body")):
        return ReferenceDecision(value, "rejected", False, ("unstable_page_scraping_not_permitted",))
    return ReferenceDecision(value, "reference_only", False, ("documented_interface_required",))


def _literal_ip(host: str) -> ipaddress._BaseAddress | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _canonical_parts(value: str) -> SplitResult:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("reference URL must use http or https")
    if not parsed.hostname:
        raise ValueError("reference URL must contain a host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("reference URL must not contain userinfo")
    if parsed.fragment:
        raise ValueError("reference URL must not contain a fragment")
    host = parsed.hostname.rstrip(".").lower()
    literal = _literal_ip(host)
    if host in {"localhost", "localhost.localdomain"} or literal is not None and (
        literal.is_private or literal.is_loopback or literal.is_link_local or literal.is_multicast
        or literal.is_unspecified or literal.is_reserved
    ):
        raise ValueError("reference URL targets a local or reserved address")
    if parsed.port is not None and not (1 <= parsed.port <= 65535):
        raise ValueError("reference URL port is invalid")
    # Rebuild without credentials, fragments, or host spelling ambiguity.
    netloc = host if parsed.port is None else f"{host}:{parsed.port}"
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=netloc)


def validate_reference(
    value: str,
    *,
    permit_resolution: bool = False,
    allowed_hosts: frozenset[str] = frozenset(),
) -> ReferenceDecision:
    """Validate a submitted URL without performing network access.

    Resolution is admitted only when explicitly enabled and the normalized
    hostname exactly matches an allowlisted host.  DNS names are not resolved
    here; the eventual connector must re-check the resolved address.
    """

    try:
        parsed = _canonical_parts(value)
    except (TypeError, ValueError) as exc:
        return ReferenceDecision(str(value), "rejected", False, (str(exc),))
    canonical = parsed.geturl()
    host = parsed.hostname.rstrip(".").lower() if parsed.hostname else ""
    if not permit_resolution:
        return ReferenceDecision(canonical, "reference_only", False, ("resolution_not_permitted",))
    normalized_allowlist = frozenset(item.rstrip(".").lower() for item in allowed_hosts)
    if host not in normalized_allowlist:
        return ReferenceDecision(canonical, "reference_only", False, ("host_not_allowlisted",))
    return ReferenceDecision(canonical, "resolution_permitted", True, ("explicit_policy_and_allowlist",))


def validate_resolved_addresses(addresses: Iterable[str]) -> tuple[str, ...]:
    """Reject unsafe DNS results immediately before a network connection.

    The caller must pass every address returned by its resolver.  An empty
    result is rejected, and one unsafe address rejects the complete resolution
    set so a resolver cannot bypass the policy through address ordering.
    """

    normalized = tuple(str(address).strip() for address in addresses)
    if not normalized:
        raise ValueError("DNS resolution returned no addresses")
    parsed: list[str] = []
    for address in normalized:
        try:
            value = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError("DNS resolution returned a non-IP address") from exc
        if (
            value.is_private
            or value.is_loopback
            or value.is_link_local
            or value.is_multicast
            or value.is_unspecified
            or value.is_reserved
        ):
            raise ValueError("DNS resolution returned a local or reserved address")
        parsed.append(value.compressed)
    return tuple(sorted(set(parsed)))
