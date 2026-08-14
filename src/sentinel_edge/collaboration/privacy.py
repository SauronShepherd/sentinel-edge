"""Privacy transformation applied before collaborative signal persistence.

Collaborative data is deliberately event-level and pseudonymous.  Exact local
coordinates/identities are accepted only as local inputs to this module and are
never returned in the collaborative contracts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import hmac

from .models import CorrelationDomain, Hazard


_PRIMARY_DOMAIN_KIND: dict[str, str] = {
    "earthquake": "spatial_cell",
    "wildfire": "observation_area",
    "flood": "catchment",
    "landslide": "monitored_site",
}
_BUCKET_SECONDS: dict[str, int] = {
    "earthquake": 5,
    "wildfire": 60,
    "flood": 300,
    "landslide": 300,
}


def location_trust_decision(*, location_present: bool, source_verified: bool) -> tuple[bool, str]:
    """Exact or coarse location is contextual evidence, never source verification."""
    if source_verified:
        return True, "source_verified_independently"
    if location_present:
        return False, "location_cannot_verify_source"
    return False, "source_unverified"


def pseudonymous_node_id(*, local_secret: str) -> str:
    if not local_secret:
        raise ValueError("NODE_SECRET_REQUIRED")
    return sha256(("sentinel-collaboration-node:" + local_secret).encode()).hexdigest()[:32]


def coarsen_domain(*, kind: str, latitude: float | None = None, longitude: float | None = None, coarse_precision: int = 1, explicit_id: str | None = None) -> CorrelationDomain:
    if explicit_id:
        return CorrelationDomain(kind=kind, id=explicit_id)
    if latitude is None or longitude is None:
        raise ValueError("DOMAIN_COORDINATES_REQUIRED")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("DOMAIN_COORDINATES_INVALID")
    if coarse_precision < 0 or coarse_precision > 3:
        raise ValueError("DOMAIN_PRECISION_UNSUPPORTED")
    scale = 10**coarse_precision
    coarse_lat = round(latitude * scale) / scale
    coarse_lon = round(longitude * scale) / scale
    # The ID is stable and opaque; it does not expose decimal coordinates.
    opaque = sha256(f"{kind}:{coarse_lat:.{coarse_precision}f}:{coarse_lon:.{coarse_precision}f}".encode()).hexdigest()[:24]
    return CorrelationDomain(kind=kind, id=f"domain:{opaque}")


class CollaborationPrivacyTransformer:
    """Hazard-aware privacy transformer used by outbound signal generation.

    ``local_location_ref`` and ``node_identity_ref`` are local-only references.
    HMAC-derived outputs ensure neither value is embedded in collaborative data.
    The engineering bucket sizes are demo policy defaults, not scientific
    operational thresholds.
    """

    def __init__(self, *, derivation_secret: str) -> None:
        if not derivation_secret:
            raise ValueError("COLLABORATION_DERIVATION_SECRET_REQUIRED")
        self._key = derivation_secret.encode("utf-8")

    def _opaque(self, namespace: str, value: str) -> str:
        digest = hmac.new(self._key, f"{namespace}:{value}".encode("utf-8"), "sha256").hexdigest()
        return digest[:32]

    def derive_domain(
        self,
        *,
        hazard: Hazard,
        local_location_ref: str | None,
        local_sensor_context_ref: str | None = None,
    ) -> CorrelationDomain:
        if not local_location_ref and not local_sensor_context_ref:
            return CorrelationDomain(kind="unknown", id=f"unknown:{self._opaque('domain', str(hazard))[:20]}")
        context = local_sensor_context_ref or local_location_ref or "unknown"
        kind = _PRIMARY_DOMAIN_KIND[str(hazard)]
        # An explicitly classified local context may select another compatible
        # hazard domain while still hashing the private local reference.
        prefixes = {
            "camera_sector:": "camera_sector",
            "observation_area:": "observation_area",
            "river_reach:": "river_reach",
            "catchment:": "catchment",
            "slope:": "slope",
            "monitored_site:": "monitored_site",
            "spatial_cell:": "spatial_cell",
        }
        for prefix, candidate in prefixes.items():
            if context.startswith(prefix):
                kind = candidate
                break
        opaque = self._opaque(f"{hazard}:{kind}", context)
        return CorrelationDomain(kind=kind, id=f"domain:{opaque[:24]}", domain_policy_id="collab-demo-v1")

    def pseudonymize_node(self, node_identity_ref: str) -> str:
        if not node_identity_ref:
            raise ValueError("NODE_IDENTITY_REF_REQUIRED")
        return self._opaque("node", node_identity_ref)

    def bucket_time(self, *, hazard: Hazard, event_time: datetime) -> datetime:
        if event_time.tzinfo is None:
            raise ValueError("EVENT_TIME_TIMEZONE_REQUIRED")
        stamp = event_time.astimezone(timezone.utc)
        seconds = _BUCKET_SECONDS[str(hazard)]
        epoch = int(stamp.timestamp())
        bucket = epoch - (epoch % seconds)
        return datetime.fromtimestamp(bucket, tz=timezone.utc)
