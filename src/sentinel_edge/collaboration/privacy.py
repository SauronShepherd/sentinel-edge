"""Privacy transformation applied before collaborative signal persistence."""
from __future__ import annotations

from hashlib import sha256

from .models import CorrelationDomain


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
