from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinel_edge.domain.models import CriticalityTier, HazardKind, ResourceSnapshot, RuntimeMode, WorkloadSpec
from sentinel_edge.runtime import VirtualClock, WorkloadScheduler
from sentinel_edge.runtime.clip import TriggerClipBuffer
from sentinel_edge.domain.models import ImuSample
from sentinel_edge.qualification import fixed_rate_imu_windows, scan_removed_armnn, verify_judge_fixture_bundle


def spec(name: str, tier: CriticalityTier, *, max_deferral_ms: int = 100) -> WorkloadSpec:
    return WorkloadSpec(
        workload_id=name,
        hazard=HazardKind.EARTHQUAKE if tier == CriticalityTier.A_IMMEDIATE else HazardKind.FLOOD,
        tier=tier,
        period_ms=100,
        deadline_ms=50,
        max_deferral_ms=max_deferral_ms,
        estimated_cost_ms=5,
        memory_mb=16,
        profile_id=f"{name}-profile",
    )


def resources(**updates) -> ResourceSnapshot:
    values = dict(cpu_pressure=0.2, memory_pressure=0.2, io_pressure=0.2, temperature_c=45, available_memory_mb=256)
    values.update(updates)
    return ResourceSnapshot(**values)


def test_wall_clock_step_does_not_change_monotonic_deadline_order() -> None:
    clock = VirtualClock(datetime(2026, 8, 2, tzinfo=timezone.utc))
    scheduler = WorkloadScheduler(clock=clock)
    scheduler.register(spec("first", CriticalityTier.B_URGENT))
    scheduler.register(spec("second", CriticalityTier.B_URGENT))
    scheduler.submit("first", {})
    clock.advance_ms(5)
    scheduler.submit("second", {})
    clock.step_utc(timedelta(hours=-12))
    assert scheduler.dispatch(resources()).workload.workload_id == "first"


def test_overload_and_max_deferral_are_visible_and_accounted() -> None:
    clock = VirtualClock()
    scheduler = WorkloadScheduler(clock=clock, mode=RuntimeMode.BENCHMARK)
    scheduler.register(spec("background", CriticalityTier.D_PERIODIC, max_deferral_ms=10))
    scheduler.submit("background", {})
    overloaded = resources(cpu_pressure=0.99)
    assert scheduler.dispatch(overloaded) is None
    assert scheduler.snapshot().deferred == ("background",)
    clock.advance_ms(11)
    assert scheduler.dispatch(overloaded) is None
    snapshot = scheduler.snapshot()
    assert snapshot.overloaded is True
    assert scheduler.queued == 0
    assert scheduler.opportunities.reconcile()["balanced"] is True
    assert scheduler.opportunities.counts()["skipped"] == 1


def test_forced_scan_cadence_overrides_lower_tier_deferral() -> None:
    clock = VirtualClock()
    scheduler = WorkloadScheduler(clock=clock)
    forced = spec("wildfire-stage2", CriticalityTier.C_TIMELY)
    forced = forced.model_copy(update={"forced_scan_ms": 20, "max_deferral_ms": 1000})
    scheduler.register(forced)
    scheduler.submit("wildfire-stage2", {})
    assert scheduler.dispatch(resources(cpu_pressure=0.99)) is None
    clock.advance_ms(21)
    job = scheduler.dispatch(resources(cpu_pressure=0.99))
    assert job is not None
    assert "forced_scan_due" in scheduler.snapshot().reason_codes


def test_wildfire_stage2_forced_deadline_is_admitted_under_overload() -> None:
    clock = VirtualClock()
    scheduler = WorkloadScheduler(clock=clock)
    forced = spec("wildfire-stage2-deadline", CriticalityTier.C_TIMELY).model_copy(
        update={"forced_scan_ms": 20, "max_deferral_ms": 5000}
    )
    scheduler.register(forced)
    scheduler.submit("wildfire-stage2-deadline", {})

    assert scheduler.dispatch(resources(cpu_pressure=0.99)) is None
    clock.advance_ms(20)
    job = scheduler.dispatch(resources(cpu_pressure=0.99))

    assert job is not None
    assert job.workload.workload_id == "wildfire-stage2-deadline"
    assert "forced_scan_due" in scheduler.snapshot().reason_codes


def test_flood_and_landslide_cannot_starve_past_bounded_deferral() -> None:
    clock = VirtualClock()
    scheduler = WorkloadScheduler(clock=clock)
    flood = spec("flood-starvation", CriticalityTier.C_TIMELY, max_deferral_ms=10)
    landslide = flood.model_copy(update={"workload_id": "landslide-starvation", "hazard": HazardKind.LANDSLIDE})
    scheduler.register(flood)
    scheduler.register(landslide)
    scheduler.submit("flood-starvation", {})
    scheduler.submit("landslide-starvation", {})
    overloaded = resources(cpu_pressure=0.99)

    assert scheduler.dispatch(overloaded) is None
    clock.advance_ms(11)
    first = scheduler.dispatch(overloaded)
    second = scheduler.dispatch(overloaded)

    assert {first.workload.workload_id if first else None, second.workload.workload_id if second else None} == {
        "flood-starvation",
        "landslide-starvation",
    }


def test_fresh_context_reallocates_future_cadence_with_reason() -> None:
    scheduler = WorkloadScheduler(clock=VirtualClock())
    original = spec("landslide-context", CriticalityTier.C_TIMELY)
    scheduler.register(original)

    updated = scheduler.reallocate_cadence(
        "landslide-context", multiplier=2.0, reason_code="rainfall_context_elevated"
    )

    assert updated.period_ms == 50
    assert scheduler.snapshot().reason_codes == ("cadence_reallocated:rainfall_context_elevated",)
    assert scheduler.submit("landslide-context", {}).workload.period_ms == 50


def test_trigger_clip_retains_bounded_pre_and_post_window() -> None:
    clip = TriggerClipBuffer[int](pre_trigger_frames=3, post_trigger_frames=2)
    for frame in range(5):
        assert clip.append(frame) is None
    clip.trigger()
    assert clip.append(5) is None
    retained = clip.append(6)

    assert retained is not None
    assert retained.frames == (2, 3, 4, 5, 6)
    assert retained.pre_trigger_count == 3
    assert retained.post_trigger_count == 2


def test_fixed_rate_imu_windows_expose_sequence_and_timing_gaps() -> None:
    samples = tuple(
        ImuSample(
            sequence=index + (1 if index >= 3 else 0),
            monotonic_ns=index * 10_000_000,
            x=0.0,
            y=0.0,
            z=9.81,
            unit="m/s2",
        )
        for index in range(4)
    )
    windows = fixed_rate_imu_windows(samples, window_size=4, expected_rate_hz=100.0)
    assert len(windows) == 1
    assert windows[0].sequence_gaps == 1
    assert windows[0].timing_gaps == 0
    assert windows[0].complete is False


def test_fixed_rate_imu_windows_retain_complete_waveform_window() -> None:
    samples = tuple(
        ImuSample(
            sequence=index,
            monotonic_ns=index * 10_000_000,
            x=0.0,
            y=0.0,
            z=9.81,
            unit="m/s2",
        )
        for index in range(4)
    )
    window = fixed_rate_imu_windows(samples, window_size=4, expected_rate_hz=100.0)[0]
    assert window.complete is True
    assert tuple(sample.sequence for sample in window.samples) == (0, 1, 2, 3)


def test_bundled_judge_fixture_set_is_complete_and_offline() -> None:
    report = verify_judge_fixture_bundle("fixtures")
    assert report["valid"] is True
    assert report["missing"] == []
    assert report["network_markers"] == []

    required = [
        Path("fixtures/scenarios/simultaneous-event.json"),
        Path("fixtures/scenarios/benchmark-open-loop.json"),
        Path("fixtures/camera/wildfire-camera-5fps-development.jsonl"),
        Path("fixtures/models/wildfire-smoke-quality.manifest.json"),
        Path("fixtures/sensors/earthquake-imu-chain-v1.signed.json"),
    ]
    forbidden = (b"BEGIN PRIVATE KEY", b"decrypt", b"passphrase", b"private_media", b"restricted_media")
    for path in required:
        payload = path.read_bytes().lower()
        assert not any(marker.lower() in payload for marker in forbidden), path


def test_runtime_configuration_excludes_removed_armnn_provider() -> None:
    report = scan_removed_armnn("src")
    assert report["valid"] is True
    assert report["findings"] == []


def test_scheduler_records_normal_policy_by_default() -> None:
    scheduler = WorkloadScheduler(clock=VirtualClock())
    assert scheduler.snapshot().scheduling_policy == "normal"
