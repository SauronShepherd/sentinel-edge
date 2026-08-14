from pathlib import Path

import pytest

from sentinel_edge.collector.physical import (
    PhysicalSourceUnavailable,
    read_physical_camera_frames,
    read_physical_imu_samples,
)


def test_physical_imu_rejects_regular_fixture_file(tmp_path: Path) -> None:
    source = tmp_path / "imu.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    with pytest.raises(PhysicalSourceUnavailable, match="POSIX/Linux|character device"):
        read_physical_imu_samples(source)


def test_physical_camera_rejects_regular_fixture_file(tmp_path: Path) -> None:
    source = tmp_path / "camera.raw"
    source.write_bytes(b"frame")
    with pytest.raises(PhysicalSourceUnavailable, match="POSIX/Linux|character device"):
        read_physical_camera_frames(source, frame_decoder=lambda _: None)


def test_physical_adapter_bounds_are_validated(tmp_path: Path) -> None:
    source = tmp_path / "imu.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="bounds"):
        read_physical_imu_samples(source, max_samples=0)
