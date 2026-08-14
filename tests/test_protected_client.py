from sentinel_edge.gateway.protected_client import authorize_restricted_offline_evidence


def test_restricted_offline_evidence_requires_declared_native_profile() -> None:
    admitted = authorize_restricted_offline_evidence(profile_id="protected-native-client-v1",
        native_client=True, authenticated=True, protected_storage=True)
    assert admitted.allowed is True
    for kwargs in (
        {"profile_id": "web-client", "native_client": True, "authenticated": True, "protected_storage": True},
        {"profile_id": "protected-native-client-v1", "native_client": False, "authenticated": True, "protected_storage": True},
        {"profile_id": "protected-native-client-v1", "native_client": True, "authenticated": False, "protected_storage": True},
        {"profile_id": "protected-native-client-v1", "native_client": True, "authenticated": True, "protected_storage": False},
    ):
        assert authorize_restricted_offline_evidence(**kwargs).allowed is False
