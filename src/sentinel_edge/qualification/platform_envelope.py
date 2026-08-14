from __future__ import annotations

import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import CapabilityState
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


class PlatformRuntimeEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-platform-runtime-envelope/1.0"] = Field(
        default="sentinel-edge-platform-runtime-envelope/1.0", alias="schema", serialization_alias="schema"
    )
    envelope_id: str
    observed_at: datetime
    expires_at: datetime
    board_model: str | None
    machine: str
    bootloader_identity: str | None
    firmware_identity: str | None
    kernel_release: str
    kernel_image_sha256: str | None
    os_image_identity: str | None
    cpu_features: tuple[str, ...]
    runtime_identities: dict[str, str]
    driver_identities: dict[str, str]
    hardening_identities: dict[str, str]
    benchmark_host_sha256: str
    host_trust_sha256: str
    source_class: Literal["observed", "fixture"]

    @field_validator("envelope_id", "machine", "kernel_release", "benchmark_host_sha256", "host_trust_sha256")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("platform envelope fields must not be blank")
        return value

    @model_validator(mode="after")
    def positive_window(self) -> "PlatformRuntimeEnvelope":
        if self.expires_at <= self.observed_at:
            raise ValueError("platform runtime envelope must have positive validity")
        return self


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip("\x00\n ")
    except OSError:
        return None


def observe_cpu_features() -> tuple[str, ...]:
    features: set[str] = set()
    text = _read_text(Path("/proc/cpuinfo")) or ""
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() in {"features", "flags"}:
            features.update(value.strip().lower().split())
    return tuple(sorted(features))


def build_platform_runtime_envelope(
    *,
    envelope_id: str,
    benchmark_host_report: dict[str, Any],
    host_trust_report: dict[str, Any],
    runtime_identities: dict[str, str],
    driver_identities: dict[str, str],
    hardening_identities: dict[str, str],
    observed_at: datetime,
    expires_at: datetime,
    source_class: Literal["observed", "fixture"] = "observed",
) -> PlatformRuntimeEnvelope:
    kernel_path = Path("/boot") / f"vmlinuz-{platform.release()}"
    return PlatformRuntimeEnvelope(
        envelope_id=envelope_id,
        observed_at=observed_at,
        expires_at=expires_at,
        board_model=host_trust_report.get("board_model"),
        machine=str(benchmark_host_report.get("machine") or platform.machine()),
        bootloader_identity=(host_trust_report.get("bootloader") or {}).get("stdout"),
        firmware_identity=(host_trust_report.get("firmware") or {}).get("raspberry_pi_config_sha256"),
        kernel_release=str(benchmark_host_report.get("kernel_release") or platform.release()),
        kernel_image_sha256=sha256_file(kernel_path) if kernel_path.is_file() else None,
        os_image_identity=host_trust_report.get("root_filesystem", {}).get("mountinfo_sha256"),
        cpu_features=observe_cpu_features(),
        runtime_identities=dict(sorted(runtime_identities.items())),
        driver_identities=dict(sorted(driver_identities.items())),
        hardening_identities=dict(sorted(hardening_identities.items())),
        benchmark_host_sha256=sha256_bytes(canonical_json_bytes(benchmark_host_report)),
        host_trust_sha256=sha256_bytes(canonical_json_bytes(host_trust_report)),
        source_class=source_class,
    )


def evaluate_platform_runtime_envelope(
    envelope: PlatformRuntimeEnvelope | dict[str, Any],
    *,
    expected: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    item = envelope if isinstance(envelope, PlatformRuntimeEnvelope) else PlatformRuntimeEnvelope.model_validate(envelope)
    failures: list[str] = []
    limitations: list[str] = []
    if now >= item.expires_at:
        failures.append("platform_envelope_expired")
    exact_fields = (
        "board_model", "machine", "bootloader_identity", "firmware_identity", "kernel_release",
        "kernel_image_sha256", "os_image_identity", "benchmark_host_sha256", "host_trust_sha256",
    )
    for field in exact_fields:
        if field in expected and getattr(item, field) != expected[field]:
            failures.append(f"platform_fact_mismatch:{field}")
    for category in ("runtime_identities", "driver_identities", "hardening_identities"):
        required = expected.get(category, {})
        actual = getattr(item, category)
        for name, value in required.items():
            if name not in actual:
                failures.append(f"platform_fact_unrecorded:{category}:{name}")
            elif actual[name] != value:
                failures.append(f"platform_fact_mismatch:{category}:{name}")
    if expected.get("require_observed_source", True) and item.source_class != "observed":
        failures.append("platform_source_not_observed")
    board = (item.board_model or "").lower()
    pi5 = "raspberry pi 5" in board or expected.get("target_family") == "raspberry-pi-5"
    forbidden = {"sve", "sve2", "sme", "sme2"}
    claimed = set(str(value).lower() for value in expected.get("claimed_cpu_features", []))
    if pi5 and claimed & forbidden:
        failures.append("unsupported_raspberry_pi_5_vector_claim")
    observed_forbidden = forbidden & set(item.cpu_features)
    if pi5 and observed_forbidden:
        limitations.append("unexpected_vector_feature_observation_requires_review:" + ",".join(sorted(observed_forbidden)))
    target_qualified = not failures and item.source_class == "observed"
    state = CapabilityState.TARGET_QUALIFIED if target_qualified else CapabilityState.TESTED if not failures else CapabilityState.FAILED
    body = {
        "schema": "sentinel-edge-platform-runtime-envelope-evaluation/1.0",
        "envelope_id": item.envelope_id,
        "envelope_sha256": sha256_bytes(canonical_json_bytes(item.model_dump(mode="json", by_alias=True))),
        "state": state.value,
        "target_qualified": target_qualified,
        "qualification_inheritance_allowed": target_qualified,
        "raspberry_pi_5_vector_claim_allowed": pi5 and not (claimed & forbidden),
        "failures": sorted(set(failures)),
        "limitations": sorted(set(limitations)),
        "evaluated_at": now.isoformat(),
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}
