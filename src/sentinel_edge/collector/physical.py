"""Bounded adapters for locally attached camera and IMU devices.

These adapters deliberately stop at acquisition. They do not infer hazard state and
they never treat a regular file as a physical source. Camera frame decoding is
injected because V4L2 pixel formats and framing are device-specific; the byte
transport remains bounded and fail-closed here.
"""

from __future__ import annotations

import json
import os
import selectors
import stat
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TypeVar

from sentinel_edge.domain.models import CameraFrameSample, ImuSample


class PhysicalSourceUnavailable(RuntimeError):
    """Raised when a local physical source cannot be opened safely."""


T = TypeVar("T")


def _validate_bounds(*, max_items: int, timeout_seconds: float, max_item_bytes: int) -> None:
    if max_items <= 0 or timeout_seconds <= 0 or max_item_bytes <= 0:
        raise ValueError("capture bounds must be positive")


def _require_posix_character_device(path: str | Path) -> Path:
    source = Path(path)
    if os.name != "posix":
        raise PhysicalSourceUnavailable("physical device capture requires POSIX/Linux")
    try:
        mode = source.stat().st_mode
    except OSError as exc:
        raise PhysicalSourceUnavailable(f"physical source is unavailable: {source}") from exc
    if not stat.S_ISCHR(mode):
        raise PhysicalSourceUnavailable("physical source must be a character device")
    return source


def _bounded_ready_reads(
    source: Path,
    *,
    max_items: int,
    timeout_seconds: float,
    max_item_bytes: int,
    item_reader: Callable[[bytearray], T | None],
) -> Iterator[T]:
    _validate_bounds(
        max_items=max_items,
        timeout_seconds=timeout_seconds,
        max_item_bytes=max_item_bytes,
    )
    selector = selectors.DefaultSelector()
    buffer = bytearray()
    emitted = 0
    try:
        with source.open("rb", buffering=0) as handle:
            selector.register(handle, selectors.EVENT_READ)
            while emitted < max_items:
                ready = selector.select(timeout_seconds)
                if not ready:
                    raise PhysicalSourceUnavailable("physical source read timed out")
                chunk = os.read(handle.fileno(), min(64 * 1024, max_item_bytes + 1))
                if not chunk:
                    raise PhysicalSourceUnavailable("physical source ended before capture completed")
                buffer.extend(chunk)
                if len(buffer) > max_item_bytes:
                    raise PhysicalSourceUnavailable("physical source item exceeded configured bound")
                item = item_reader(buffer)
                if item is not None:
                    emitted += 1
                    yield item
    except PhysicalSourceUnavailable:
        raise
    except OSError as exc:
        raise PhysicalSourceUnavailable(f"physical source read failed: {source}") from exc
    finally:
        selector.close()


def read_physical_imu_samples(
    path: str | Path,
    *,
    max_samples: int = 256,
    timeout_seconds: float = 1.0,
    max_line_bytes: int = 16 * 1024,
) -> tuple[ImuSample, ...]:
    """Read newline-delimited normalized IMU samples from a local device.

    A small IIO/serial bridge can emit the normalized JSONL contract directly. Raw
    binary protocols must be decoded by that bridge before entering this boundary.
    """
    _validate_bounds(
        max_items=max_samples,
        timeout_seconds=timeout_seconds,
        max_item_bytes=max_line_bytes,
    )

    def read_item(buffer: bytearray) -> ImuSample | None:
        newline = buffer.find(b"\n")
        if newline < 0:
            if len(buffer) > max_line_bytes:
                raise PhysicalSourceUnavailable("IMU record exceeded configured bound")
            return None
        raw = bytes(buffer[:newline]).strip()
        del buffer[: newline + 1]
        if not raw:
            return None
        try:
            return ImuSample.model_validate(json.loads(raw))
        except Exception as exc:
            raise PhysicalSourceUnavailable("physical IMU record failed normalization") from exc

    return tuple(_bounded_ready_reads(
        _require_posix_character_device(path),
        max_items=max_samples,
        timeout_seconds=timeout_seconds,
        max_item_bytes=max_line_bytes,
        item_reader=read_item,
    ))


def read_physical_camera_frames(
    path: str | Path,
    *,
    frame_decoder: Callable[[bytes], CameraFrameSample | None],
    max_frames: int = 64,
    timeout_seconds: float = 1.0,
    max_frame_bytes: int = 8 * 1024 * 1024,
) -> tuple[CameraFrameSample, ...]:
    """Capture bounded camera payloads using an explicit decoder.

    ``frame_decoder`` owns device-specific framing (for example V4L2 MJPEG or
    YUYV). It must consume the complete payload passed to it or return ``None``;
    this adapter does not guess pixel formats or silently decode fixtures.
    """
    _validate_bounds(
        max_items=max_frames,
        timeout_seconds=timeout_seconds,
        max_item_bytes=max_frame_bytes,
    )

    def read_item(buffer: bytearray) -> CameraFrameSample | None:
        try:
            frame = frame_decoder(bytes(buffer))
        except Exception as exc:
            raise PhysicalSourceUnavailable("physical camera frame failed decoding") from exc
        if frame is not None:
            buffer.clear()
        return frame

    return tuple(_bounded_ready_reads(
        _require_posix_character_device(path),
        max_items=max_frames,
        timeout_seconds=timeout_seconds,
        max_item_bytes=max_frame_bytes,
        item_reader=read_item,
    ))
