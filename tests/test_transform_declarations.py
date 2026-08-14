import pytest

from sentinel_edge.geospatial.transform_declarations import TransformDeclaration, validate_transform_declaration


def test_material_transform_requires_explicit_operation_area_epoch_and_accuracy() -> None:
    declaration = TransformDeclaration("EPSG:4326", "EPSG:25830", "pipeline:pinned", "Iberia", 2026.0, 0.25)
    assert validate_transform_declaration(declaration) == (True, ())


def test_ballpark_or_missing_epoch_is_not_qualified() -> None:
    declaration = TransformDeclaration("EPSG:4326", "EPSG:25830", "ballpark:fallback", "global", None, 100.0)
    ok, reasons = validate_transform_declaration(declaration)
    assert not ok
    assert {"ballpark_operation_not_allowed", "coordinate_epoch_unresolved"} == set(reasons)


def test_incomplete_declaration_is_rejected() -> None:
    with pytest.raises(ValueError):
        TransformDeclaration("", "EPSG:25830", "pipeline", "global", 2026.0, 1.0)
