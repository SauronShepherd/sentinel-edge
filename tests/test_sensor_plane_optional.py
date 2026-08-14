from sentinel_edge.app import compose
from sentinel_edge.collector import resolve_sensor_plane_availability


def test_pi_only_mode_is_complete_without_optional_sensor_plane() -> None:
    status = resolve_sensor_plane_availability(enabled=False, available=False)
    assert status.operating_mode == "pi_only"
    assert status.release_dependency is False
    assert "sensor_plane_unavailable" not in status.reason_codes
    components = compose()
    assert components.collector is not None


def test_fixture_mode_is_explicit_and_optional_plane_never_blocks_release_path() -> None:
    status = resolve_sensor_plane_availability(enabled=True, available=False, fixture_mode=True)
    assert status.operating_mode == "fixture"
    assert status.release_dependency is False
    assert status.reason_codes == ("fixture_mode", "sensor_plane_optional")


def test_enabled_available_plane_is_an_optional_enhancement() -> None:
    status = resolve_sensor_plane_availability(enabled=True, available=True)
    assert status.operating_mode == "sensor_plane"
    assert status.release_dependency is False
