from sentinel_edge.storage.artifact_governance import ArtifactPolicy, authorize_artifact_read


def test_restricted_artifact_read_requires_owner_integrity_size_and_role() -> None:
    policy = ArtifactPolicy.incident_evidence(restricted=True)
    allowed = authorize_artifact_read(
        policy, owner="owner-1", requester="owner-1", verification_role=True,
        integrity_valid=True, observed_bytes=10, max_bytes=100,
    )
    assert allowed.allowed is True
    assert allowed.disclose_digest is True


def test_wrong_owner_integrity_oversize_and_unauthorized_reads_are_denied() -> None:
    policy = ArtifactPolicy.incident_evidence(restricted=True)
    denied = authorize_artifact_read(
        policy, owner="owner-1", requester="other", verification_role=False,
        integrity_valid=False, observed_bytes=101, max_bytes=100,
    )
    assert denied.allowed is False
    assert {"wrong_owner", "integrity_failed", "oversize", "restricted_read_unauthorized"} <= set(denied.reason_codes)
    assert denied.disclose_digest is False
