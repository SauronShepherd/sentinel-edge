from sentinel_edge.qualification.privacy_transform import PrePersistenceTransform


def test_pre_persistence_transform_redacts_sensitive_fields() -> None:
    result = PrePersistenceTransform(coordinate_precision_digits=2).apply(
        coordinates=(12.3456, -7.8912), sender_identity="private-user")
    assert result["faces_transformed"] is True
    assert result["plates_transformed"] is True
    assert result["coordinates"] == (12.35, -7.89)
    assert result["sender_identity"] == "redacted"


def test_transform_configuration_can_preserve_nonprivate_coordinates_only() -> None:
    result = PrePersistenceTransform(redact_private_sender_identity=False).apply(sender_identity="operator")
    assert result["sender_identity"] == "operator"
