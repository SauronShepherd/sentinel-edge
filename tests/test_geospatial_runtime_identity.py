import pytest

from sentinel_edge.geospatial.runtime_identity import ProjRuntimeIdentity, qualify_proj_runtime


def test_runtime_identity_requires_actual_library_database_and_grid_digests() -> None:
    identity = ProjRuntimeIdentity("3.7", "libproj.so.25", "/usr/share/proj", "a" * 64, ("b" * 64,))
    assert qualify_proj_runtime(identity, required_grid_digests=frozenset({"b" * 64})) == (True, ())


def test_missing_required_grid_is_not_qualified() -> None:
    identity = ProjRuntimeIdentity("3.7", "libproj.so.25", "/usr/share/proj", "a" * 64, ())
    ok, reasons = qualify_proj_runtime(identity, required_grid_digests=frozenset({"b" * 64}))
    assert not ok and reasons == (f"required_grid_missing:{'b' * 64}",)


def test_inferred_identity_is_rejected() -> None:
    with pytest.raises(ValueError):
        ProjRuntimeIdentity("", "package-name", "", "a" * 64, ())
