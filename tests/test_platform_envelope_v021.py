from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification import PlatformRuntimeEnvelope, evaluate_platform_runtime_envelope

NOW = datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)


def _envelope(**overrides):
    values = dict(
        envelope_id="rpi5-runtime-v1",
        observed_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(days=1),
        board_model="Raspberry Pi 5 Model B Rev 1.0",
        machine="aarch64",
        bootloader_identity="2026-07-01",
        firmware_identity="firmware-sha",
        kernel_release="6.12.0-rpi",
        kernel_image_sha256="a" * 64,
        os_image_identity="os-image-v1",
        cpu_features=("asimd", "crc32"),
        runtime_identities={"onnxruntime": "1.22.0", "sentinel-edge": "0.21.0"},
        driver_identities={"imu": "bmi270-driver-v1"},
        hardening_identities={"lockdown": "integrity", "lsm": "landlock,apparmor"},
        benchmark_host_sha256="b" * 64,
        host_trust_sha256="c" * 64,
        source_class="observed",
    )
    values.update(overrides)
    return PlatformRuntimeEnvelope(**values)


def test_exact_runtime_envelope_qualifies_without_vector_overclaim() -> None:
    env = _envelope()
    report = evaluate_platform_runtime_envelope(env, expected={
        "target_family": "raspberry-pi-5",
        "machine": "aarch64",
        "runtime_identities": {"onnxruntime": "1.22.0"},
        "driver_identities": {"imu": "bmi270-driver-v1"},
        "hardening_identities": {"lockdown": "integrity"},
        "claimed_cpu_features": ["asimd"],
    }, now=NOW)
    assert report["target_qualified"] is True
    assert report["raspberry_pi_5_vector_claim_allowed"] is True


def test_missing_fact_and_sve_claim_fail_closed() -> None:
    report = evaluate_platform_runtime_envelope(_envelope(), expected={
        "target_family": "raspberry-pi-5",
        "runtime_identities": {"onnxruntime": "1.23.0", "compiler": "missing"},
        "claimed_cpu_features": ["sve", "sme2"],
    }, now=NOW)
    assert report["target_qualified"] is False
    assert "unsupported_raspberry_pi_5_vector_claim" in report["failures"]
    assert "platform_fact_unrecorded:runtime_identities:compiler" in report["failures"]


def test_fixture_or_expired_envelope_cannot_inherit_target_status() -> None:
    fixture = evaluate_platform_runtime_envelope(_envelope(source_class="fixture"), expected={}, now=NOW)
    assert fixture["target_qualified"] is False
    assert "platform_source_not_observed" in fixture["failures"]
    expired = evaluate_platform_runtime_envelope(_envelope(expires_at=NOW), expected={}, now=NOW)
    assert "platform_envelope_expired" in expired["failures"]
