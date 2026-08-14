"""Versioned, purpose-bound digest profiles for cross-artifact comparisons."""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sentinel_edge.security.digests import canonical_json_bytes


class DigestComparison(StrEnum):
    EQUAL = "equal"
    DIFFERENT = "different"
    INCOMPLETE = "incomplete_evidence"


@dataclass(frozen=True)
class DigestProfile:
    profile_id: str
    version: int
    purpose: str
    privacy_class: str
    algorithm: str = "sha256"
    canonicalization: str = "canonical-json-v1"
    key_version: str | None = None

    def __post_init__(self) -> None:
        if not self.profile_id.strip() or self.version < 1 or not self.purpose.strip() or not self.privacy_class.strip():
            raise ValueError("digest profile identity and purpose are required")
        if self.algorithm != "sha256" or self.canonicalization != "canonical-json-v1":
            raise ValueError("unsupported digest algorithm or canonicalization")
        if self.key_version is not None and not self.key_version.strip():
            raise ValueError("key_version cannot be blank")


@dataclass(frozen=True)
class ProfiledDigest:
    profile: DigestProfile
    value: str


def digest_value(value: Any, profile: DigestProfile, *, key: bytes | None = None) -> ProfiledDigest:
    if profile.key_version and not key:
        raise ValueError("key material is required by the digest profile")
    if not profile.key_version and key is not None:
        raise ValueError("unkeyed profile cannot accept key material")
    data = canonical_json_bytes(value)
    if key is None:
        value_hex = hashlib.sha256(data).hexdigest()
    else:
        value_hex = hmac.new(key, profile.purpose.encode("utf-8") + b"\0" + data, hashlib.sha256).hexdigest()
    return ProfiledDigest(profile, value_hex)


def compare_digests(left: ProfiledDigest, right: ProfiledDigest) -> DigestComparison:
    if left.profile != right.profile:
        return DigestComparison.INCOMPLETE
    return DigestComparison.EQUAL if hmac.compare_digest(left.value, right.value) else DigestComparison.DIFFERENT
