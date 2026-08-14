"""Backward-compatible release-candidate API.

The canonical implementation lives in :mod:`sentinel_edge.release`; this
module preserves the documented import path used by the remediation audit and
older integrations.
"""

from sentinel_edge.release import (
    sign_release_candidate,
    verify_release_candidate,
    write_release_candidate,
)

__all__ = [
    "sign_release_candidate",
    "verify_release_candidate",
    "write_release_candidate",
]
