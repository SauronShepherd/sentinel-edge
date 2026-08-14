import pytest

from sentinel_edge.geospatial.pin_manifest import TransformEnvironmentPin


def test_transform_environment_pin_contains_all_material_inputs() -> None:
    pin = TransformEnvironmentPin("3.7", "9.3", "a" * 64, ("b" * 64,), "offline-best-qualified-v1", "c" * 64)
    assert pin.as_dict()["transform_policy"] == "offline-best-qualified-v1"


def test_transform_environment_pin_rejects_missing_identity() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        TransformEnvironmentPin("", "9.3", "a" * 64, (), "policy", "c" * 64)
