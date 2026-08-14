from __future__ import annotations

import json
import math
import statistics
import stat
from dataclasses import dataclass
from pathlib import Path

from sentinel_edge.domain.models import CapabilityState, ImuSample, SensorCommissioningReport, SensorKind
from sentinel_edge.security import sha256_file


@dataclass(frozen=True)
class ImuWindow:
    """A fixed-size IMU window whose sequence/timing gaps remain explicit."""

    samples: tuple[ImuSample, ...]
    expected_interval_ns: int
    sequence_gaps: int
    timing_gaps: int

    @property
    def complete(self) -> bool:
        return bool(self.samples) and not self.sequence_gaps and not self.timing_gaps


def fixed_rate_imu_windows(
    samples: tuple[ImuSample, ...],
    *,
    window_size: int,
    expected_rate_hz: float,
) -> tuple[ImuWindow, ...]:
    """Partition samples without dropping gaps or silently repairing timestamps."""
    if window_size <= 0 or expected_rate_hz <= 0:
        raise ValueError("window_size and expected_rate_hz must be positive")
    interval = round(1_000_000_000 / expected_rate_hz)
    windows: list[ImuWindow] = []
    for start in range(0, len(samples), window_size):
        chunk = tuple(samples[start : start + window_size])
        sequence_gaps = sum(
            current.sequence != previous.sequence + 1
            for previous, current in zip(chunk, chunk[1:])
        )
        timing_gaps = sum(
            current.monotonic_ns - previous.monotonic_ns != interval
            for previous, current in zip(chunk, chunk[1:])
        )
        windows.append(ImuWindow(chunk, interval, sequence_gaps, timing_gaps))
    return tuple(windows)


def load_imu_samples(path: str | Path) -> tuple[ImuSample, ...]:
    source = Path(path)
    samples: list[ImuSample] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                samples.append(ImuSample.model_validate(json.loads(line)))
            except Exception as exc:  # pydantic exposes useful context in the wrapped message
                raise ValueError(f"invalid IMU sample at line {line_no}: {exc}") from exc
    return tuple(samples)


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def commission_imu(
    path: str | Path,
    *,
    source_id: str,
    requested_rate_hz: float,
    minimum_samples: int = 100,
    rate_tolerance_fraction: float = 0.05,
    maximum_gap_factor: float = 2.0,
    saturation_abs: float = 160.0,
) -> SensorCommissioningReport:
    source = Path(path)
    samples = load_imu_samples(source)
    reasons: list[str] = []
    physical_source = False
    try:
        resolved = source.resolve()
        mode = source.stat().st_mode
        physical_source = resolved.as_posix().startswith("/dev/") and stat.S_ISCHR(mode)
    except OSError:
        physical_source = False
    if len(samples) < minimum_samples:
        reasons.append("insufficient_samples")
    intervals_ns: list[int] = []
    sequence_gaps = 0
    non_monotonic = 0
    units = {sample.unit for sample in samples}
    saturation_samples = 0
    for previous, current in zip(samples, samples[1:]):
        delta = current.monotonic_ns - previous.monotonic_ns
        if delta <= 0:
            non_monotonic += 1
        else:
            intervals_ns.append(delta)
        if current.sequence != previous.sequence + 1:
            sequence_gaps += 1
    for sample in samples:
        if max(abs(sample.x), abs(sample.y), abs(sample.z)) >= saturation_abs:
            saturation_samples += 1
    duration_seconds = 0.0
    if len(samples) >= 2 and samples[-1].monotonic_ns > samples[0].monotonic_ns:
        duration_seconds = (samples[-1].monotonic_ns - samples[0].monotonic_ns) / 1_000_000_000
    observed_rate = (len(samples) - 1) / duration_seconds if duration_seconds > 0 else 0.0
    rate_error = abs(observed_rate - requested_rate_hz) / requested_rate_hz
    expected_ms = 1000.0 / requested_rate_hz
    intervals_ms = [value / 1_000_000 for value in intervals_ns]
    maximum_gap = max(intervals_ms, default=0.0)
    median_ms = statistics.median(intervals_ms) if intervals_ms else 0.0
    jitter = [abs(value - median_ms) for value in intervals_ms]
    p99_jitter = _percentile(jitter, 0.99)
    if non_monotonic:
        reasons.append("non_monotonic_sampling_clock")
    if sequence_gaps:
        reasons.append("sequence_gaps")
    if len(units) != 1:
        reasons.append("unit_inconsistent")
    elif units and next(iter(units)) not in {"m/s2", "m/s^2"}:
        reasons.append("unsupported_unit")
    if rate_error > rate_tolerance_fraction:
        reasons.append("sampling_rate_out_of_tolerance")
    if maximum_gap > expected_ms * maximum_gap_factor:
        reasons.append("sampling_gap_exceeds_limit")
    if saturation_samples:
        reasons.append("sample_saturation")
    if not physical_source:
        reasons.append("physical_device_not_proven")
    signal_quality_ok = not any(
        reason in reasons
        for reason in (
            "insufficient_samples",
            "non_monotonic_sampling_clock",
            "sequence_gaps",
            "unit_inconsistent",
            "unsupported_unit",
            "sampling_rate_out_of_tolerance",
            "sampling_gap_exceeds_limit",
            "sample_saturation",
        )
    )
    state = CapabilityState.FIELD_QUALIFIED if signal_quality_ok and physical_source else (
        CapabilityState.TESTED if signal_quality_ok else CapabilityState.FAILED
    )
    return SensorCommissioningReport(
        sensor_kind=SensorKind.IMU,
        source_id=source_id,
        source_path=str(source.resolve()),
        source_sha256=sha256_file(source),
        physical_source_proven=physical_source,
        state=state,
        sample_count=len(samples),
        duration_seconds=duration_seconds,
        requested_rate_hz=requested_rate_hz,
        observed_rate_hz=observed_rate,
        rate_error_fraction=rate_error,
        maximum_gap_ms=maximum_gap,
        p99_interval_jitter_ms=p99_jitter,
        non_monotonic_samples=non_monotonic,
        sequence_gaps=sequence_gaps,
        saturation_samples=saturation_samples,
        observed_unit=next(iter(units)) if len(units) == 1 else None,
        reason_codes=tuple(sorted(set(reasons))) if reasons else ("physical_imu_commissioned",),
    )
