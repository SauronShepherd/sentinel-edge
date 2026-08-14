import pytest

from sentinel_edge.storage.media_health import MediaHealthCapability, MediaKind


def test_media_capability_discloses_ssd_smart_limitations() -> None:
    report = MediaHealthCapability(kind=MediaKind.SSD, device="/dev/sda", smart_available=False,
        endurance_available=False, limitation="SMART probe unavailable in restricted runtime")
    assert report.smart_available is False
    assert "unavailable" in report.limitation


def test_media_health_percentage_requires_evidence() -> None:
    with pytest.raises(ValueError):
        MediaHealthCapability(kind=MediaKind.SD, device="/dev/mmcblk0", smart_available=False,
            endurance_available=False, health_percent=90, limitation="not probed")
