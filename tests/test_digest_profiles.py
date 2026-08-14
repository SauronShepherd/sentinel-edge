import pytest

from sentinel_edge.security.digest_profiles import DigestComparison, DigestProfile, compare_digests, digest_value


def test_profile_mismatch_is_incomplete_not_equal_or_different() -> None:
    a = DigestProfile("evidence", 1, "lineage", "restricted")
    b = DigestProfile("evidence", 2, "lineage", "restricted")
    assert compare_digests(digest_value({"x": 1}, a), digest_value({"x": 1}, b)) == DigestComparison.INCOMPLETE


def test_keyed_digest_is_purpose_separated_and_not_public_sha256() -> None:
    profile = DigestProfile("identity", 1, "operator-id", "secret", key_version="k1")
    first = digest_value("alice", profile, key=b"secret-key")
    second = digest_value("alice", DigestProfile("identity", 1, "telemetry", "secret", key_version="k1"), key=b"secret-key")
    assert first.value != second.value
    with pytest.raises(ValueError, match="key material"):
        digest_value("alice", profile)


def test_same_profile_preserves_equality_and_difference() -> None:
    profile = DigestProfile("artifact", 1, "content", "public")
    assert compare_digests(digest_value({"x": 1}, profile), digest_value({"x": 1}, profile)) == DigestComparison.EQUAL
    assert compare_digests(digest_value({"x": 1}, profile), digest_value({"x": 2}, profile)) == DigestComparison.DIFFERENT
