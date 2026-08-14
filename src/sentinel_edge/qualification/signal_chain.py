from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import CapabilityState, HazardKind, SensorKind
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.update import key_id


class SignalSourceClass(StrEnum):
    FIXTURE = "fixture"
    PHYSICAL = "physical"
    SIMULATED = "simulated"


class RateOperationKind(StrEnum):
    NATIVE = "native"
    DECIMATE = "decimate"
    INTERPOLATE = "interpolate"
    RESAMPLE = "resample"


class RateOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: RateOperationKind
    input_rate_hz: float = Field(gt=0)
    output_rate_hz: float = Field(gt=0)
    method: str
    anti_alias_filter_required: bool = False

    @model_validator(mode="after")
    def validate_operation(self) -> "RateOperation":
        if not self.method.strip():
            raise ValueError("rate operation method must not be blank")
        if self.kind is RateOperationKind.NATIVE and self.input_rate_hz != self.output_rate_hz:
            raise ValueError("native operation cannot change the sample rate")
        if self.kind is RateOperationKind.DECIMATE and self.output_rate_hz >= self.input_rate_hz:
            raise ValueError("decimation must reduce the sample rate")
        if self.kind is RateOperationKind.INTERPOLATE and self.output_rate_hz <= self.input_rate_hz:
            raise ValueError("interpolation must increase the sample rate")
        return self


class AntiAliasFilter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    filter_id: str
    kind: str
    cutoff_hz: float = Field(gt=0)
    order: int | None = Field(default=None, ge=1, le=256)
    evidence_sha256: str

    @field_validator("filter_id", "kind")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("filter fields must not be blank")
        return value


class SignalChainProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-signal-chain-profile/1.0"] = Field(
        default="sentinel-edge-signal-chain-profile/1.0", alias="schema", serialization_alias="schema"
    )
    profile_id: str
    hazard: HazardKind
    sensor_kind: SensorKind
    sensor_identity: str
    capture_interface: str
    driver_or_firmware_identity: str
    adc_bits: int | None = Field(default=None, ge=1, le=32)
    sample_rate_hz: float = Field(gt=0)
    full_scale: float | None = Field(default=None, gt=0)
    unit: str
    anti_alias_filter: AntiAliasFilter | None = None
    rate_operations: tuple[RateOperation, ...]
    timestamp_source: str
    maximum_timestamp_uncertainty_ms: float = Field(ge=0)
    maximum_fifo_delay_ms: float = Field(ge=0)
    maximum_rate_error_fraction: float = Field(ge=0, le=1)
    maximum_jitter_ms: float = Field(ge=0)
    maximum_gap_ms: float = Field(ge=0)
    axis_or_sector_identity: str
    preprocessing_sha256: str
    compatible_model_profile_ids: tuple[str, ...] = Field(min_length=1)
    physical_source_required_for_verified_claim: bool = True
    created_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_profile(self) -> "SignalChainProfile":
        for value in (
            self.profile_id,
            self.sensor_identity,
            self.capture_interface,
            self.driver_or_firmware_identity,
            self.unit,
            self.timestamp_source,
            self.axis_or_sector_identity,
        ):
            if not value.strip():
                raise ValueError("signal-chain fields must not be blank")
        if self.expires_at <= self.created_at:
            raise ValueError("signal-chain profile must expire after creation")
        if self.sensor_kind is SensorKind.IMU and (self.adc_bits is None or self.full_scale is None):
            raise ValueError("IMU signal chains require ADC width and full scale")
        expected = self.sample_rate_hz
        for index, operation in enumerate(self.rate_operations):
            if index == 0 and abs(operation.input_rate_hz - expected) > 1e-9:
                raise ValueError("first rate operation must start at capture rate")
            if index and abs(operation.input_rate_hz - self.rate_operations[index - 1].output_rate_hz) > 1e-9:
                raise ValueError("rate operations must form a continuous chain")
        decimation = any(item.kind is RateOperationKind.DECIMATE or item.output_rate_hz < item.input_rate_hz for item in self.rate_operations)
        if decimation and self.anti_alias_filter is None:
            raise ValueError("rate reduction requires anti-alias evidence")
        if self.anti_alias_filter is not None:
            minimum_nyquist = min([self.sample_rate_hz, *[item.output_rate_hz for item in self.rate_operations]]) / 2.0
            if self.anti_alias_filter.cutoff_hz >= minimum_nyquist:
                raise ValueError("anti-alias cutoff must remain below the minimum Nyquist frequency")
        return self


class SignedSignalChainProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-signed-signal-chain-profile/1.0"] = Field(
        default="sentinel-edge-signed-signal-chain-profile/1.0", alias="schema", serialization_alias="schema"
    )
    profile: SignalChainProfile
    profile_sha256: str
    signer_key_id: str
    signed_at: datetime
    algorithm: Literal["Ed25519"] = "Ed25519"
    signature_b64: str


class SignalChainObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_class: SignalSourceClass
    sensor_kind: SensorKind
    sensor_identity: str
    capture_interface: str
    driver_or_firmware_identity: str
    adc_bits: int | None = Field(default=None, ge=1, le=32)
    observed_rate_hz: float = Field(gt=0)
    full_scale: float | None = Field(default=None, gt=0)
    unit: str
    anti_alias_filter_id: str | None = None
    rate_operations: tuple[RateOperation, ...]
    timestamp_source: str
    timestamp_uncertainty_ms: float = Field(ge=0)
    fifo_delay_ms: float = Field(ge=0)
    rate_error_fraction: float = Field(ge=0)
    p99_jitter_ms: float = Field(ge=0)
    maximum_gap_ms: float = Field(ge=0)
    clipping_samples: int = Field(ge=0)
    saturation_samples: int = Field(ge=0)
    quantization_minimum: float | None = None
    quantization_maximum: float | None = None
    axis_or_sector_identity: str
    preprocessing_sha256: str
    commissioning_report_sha256: str
    observed_at: datetime


class SiteCommissioningRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-site-commissioning-record/1.0"] = Field(
        default="sentinel-edge-site-commissioning-record/1.0", alias="schema", serialization_alias="schema"
    )
    commissioning_id: str
    site_id: str
    sensor_identity: str
    signal_chain_profile_sha256: str
    configuration_sha256: str
    calibration_identity: str
    mounting_or_pose: str
    datum_identity: str | None = None
    camera_sector: str | None = None
    privacy_mask_sha256: str | None = None
    baseline_noise_summary: dict[str, float]
    compatible_model_profile_ids: tuple[str, ...] = Field(min_length=1)
    actor: str
    created_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_record(self) -> "SiteCommissioningRecord":
        for value in (
            self.commissioning_id,
            self.site_id,
            self.sensor_identity,
            self.calibration_identity,
            self.mounting_or_pose,
            self.actor,
        ):
            if not value.strip():
                raise ValueError("commissioning fields must not be blank")
        if self.expires_at <= self.created_at:
            raise ValueError("commissioning record must expire after creation")
        return self


class SignedSiteCommissioningRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-signed-site-commissioning-record/1.0"] = Field(
        default="sentinel-edge-signed-site-commissioning-record/1.0", alias="schema", serialization_alias="schema"
    )
    record: SiteCommissioningRecord
    record_sha256: str
    signer_key_id: str
    signed_at: datetime
    algorithm: Literal["Ed25519"] = "Ed25519"
    signature_b64: str


def sign_signal_chain_profile(
    profile: SignalChainProfile, private_key: Ed25519PrivateKey, *, signed_at: datetime | None = None
) -> SignedSignalChainProfile:
    payload = canonical_json_bytes(profile.model_dump(mode="json", by_alias=True))
    return SignedSignalChainProfile(
        profile=profile,
        profile_sha256=sha256_bytes(payload),
        signer_key_id=key_id(private_key.public_key()),
        signed_at=signed_at or datetime.now(timezone.utc),
        signature_b64=base64.b64encode(private_key.sign(payload)).decode("ascii"),
    )


def sign_site_commissioning_record(
    record: SiteCommissioningRecord, private_key: Ed25519PrivateKey, *, signed_at: datetime | None = None
) -> SignedSiteCommissioningRecord:
    payload = canonical_json_bytes(record.model_dump(mode="json", by_alias=True))
    return SignedSiteCommissioningRecord(
        record=record,
        record_sha256=sha256_bytes(payload),
        signer_key_id=key_id(private_key.public_key()),
        signed_at=signed_at or datetime.now(timezone.utc),
        signature_b64=base64.b64encode(private_key.sign(payload)).decode("ascii"),
    )


def _verify_signed(
    payload: BaseModel,
    expected_sha256: str,
    signer_key_id: str,
    signature_b64: str,
    public_key: Ed25519PublicKey,
) -> list[str]:
    raw = canonical_json_bytes(payload.model_dump(mode="json", by_alias=True))
    failures: list[str] = []
    if sha256_bytes(raw) != expected_sha256:
        failures.append("signed_payload_digest_mismatch")
    if key_id(public_key) != signer_key_id:
        failures.append("signed_payload_key_mismatch")
    try:
        public_key.verify(base64.b64decode(signature_b64, validate=True), raw)
    except (ValueError, InvalidSignature):
        failures.append("signed_payload_signature_invalid")
    return failures


def evaluate_signal_chain(
    envelope: SignedSignalChainProfile | dict[str, Any],
    public_key: Ed25519PublicKey,
    observation: SignalChainObservation | dict[str, Any],
    *,
    model_profile_id: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    signed = envelope if isinstance(envelope, SignedSignalChainProfile) else SignedSignalChainProfile.model_validate(envelope)
    observed = observation if isinstance(observation, SignalChainObservation) else SignalChainObservation.model_validate(observation)
    profile = signed.profile
    failures = _verify_signed(profile, signed.profile_sha256, signed.signer_key_id, signed.signature_b64, public_key)
    degraded: list[str] = []
    if signed.signed_at < profile.created_at:
        failures.append("signal_profile_signed_before_creation")
    if now >= profile.expires_at:
        failures.append("signal_profile_expired")
    exact_pairs = {
        "sensor_kind": (observed.sensor_kind, profile.sensor_kind),
        "sensor_identity": (observed.sensor_identity, profile.sensor_identity),
        "capture_interface": (observed.capture_interface, profile.capture_interface),
        "driver_or_firmware_identity": (observed.driver_or_firmware_identity, profile.driver_or_firmware_identity),
        "unit": (observed.unit, profile.unit),
        "timestamp_source": (observed.timestamp_source, profile.timestamp_source),
        "axis_or_sector_identity": (observed.axis_or_sector_identity, profile.axis_or_sector_identity),
        "preprocessing_sha256": (observed.preprocessing_sha256, profile.preprocessing_sha256),
    }
    for name, (actual, expected) in exact_pairs.items():
        if actual != expected:
            failures.append(f"signal_chain_mismatch:{name}")
    if observed.adc_bits != profile.adc_bits:
        failures.append("signal_chain_mismatch:adc_bits")
    if observed.full_scale != profile.full_scale:
        failures.append("signal_chain_mismatch:full_scale")
    if model_profile_id not in profile.compatible_model_profile_ids:
        failures.append("model_profile_not_signal_compatible")
    if tuple(observed.rate_operations) != tuple(profile.rate_operations):
        failures.append("rate_operation_chain_mismatch")
    expected_filter = profile.anti_alias_filter.filter_id if profile.anti_alias_filter else None
    if observed.anti_alias_filter_id != expected_filter:
        failures.append("anti_alias_filter_mismatch")
    if observed.rate_error_fraction > profile.maximum_rate_error_fraction:
        degraded.append("sample_rate_error_out_of_envelope")
    if observed.p99_jitter_ms > profile.maximum_jitter_ms:
        degraded.append("sample_jitter_out_of_envelope")
    if observed.maximum_gap_ms > profile.maximum_gap_ms:
        degraded.append("sample_gap_out_of_envelope")
    if observed.timestamp_uncertainty_ms > profile.maximum_timestamp_uncertainty_ms:
        degraded.append("timestamp_uncertainty_out_of_envelope")
    if observed.fifo_delay_ms > profile.maximum_fifo_delay_ms:
        degraded.append("fifo_delay_out_of_envelope")
    if observed.clipping_samples:
        degraded.append("clipping_detected")
    if observed.saturation_samples:
        degraded.append("saturation_detected")
    if observed.quantization_minimum is not None and observed.quantization_maximum is not None:
        if observed.quantization_minimum >= observed.quantization_maximum:
            failures.append("quantization_range_invalid")
        if profile.full_scale is not None and max(abs(observed.quantization_minimum), abs(observed.quantization_maximum)) > profile.full_scale:
            failures.append("quantization_range_exceeds_full_scale")
    physical = observed.source_class is SignalSourceClass.PHYSICAL
    compatibility_passed = not failures
    quality_passed = compatibility_passed and not degraded
    verified_claim_allowed = quality_passed and physical
    state = (
        CapabilityState.FIELD_QUALIFIED
        if verified_claim_allowed
        else CapabilityState.TESTED
        if quality_passed
        else CapabilityState.BLOCKED
        if compatibility_passed
        else CapabilityState.FAILED
    )
    body = {
        "schema": "sentinel-edge-signal-chain-evaluation/1.0",
        "profile_id": profile.profile_id,
        "profile_sha256": signed.profile_sha256,
        "model_profile_id": model_profile_id,
        "source_class": observed.source_class.value,
        "commissioning_report_sha256": observed.commissioning_report_sha256,
        "compatibility_passed": compatibility_passed,
        "quality_passed": quality_passed,
        "physical_source_proven": physical,
        "verified_claim_allowed": verified_claim_allowed,
        "latency_quality_evidence_valid": quality_passed,
        "state": state.value,
        "failures": sorted(set(failures)),
        "degraded_reason_codes": sorted(set(degraded)),
        "observed_at": observed.observed_at.isoformat(),
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}


def evaluate_site_commissioning(
    envelope: SignedSiteCommissioningRecord | dict[str, Any],
    public_key: Ed25519PublicKey,
    *,
    signal_chain_report: dict[str, Any],
    current_sensor_identity: str,
    current_configuration_sha256: str,
    current_mounting_or_pose: str,
    current_model_profile_id: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    signed = envelope if isinstance(envelope, SignedSiteCommissioningRecord) else SignedSiteCommissioningRecord.model_validate(envelope)
    record = signed.record
    failures = _verify_signed(record, signed.record_sha256, signed.signer_key_id, signed.signature_b64, public_key)
    if signed.signed_at < record.created_at:
        failures.append("commissioning_signed_before_creation")
    if now >= record.expires_at:
        failures.append("commissioning_expired")
    if signal_chain_report.get("profile_sha256") != record.signal_chain_profile_sha256:
        failures.append("commissioning_signal_profile_mismatch")
    if current_sensor_identity != record.sensor_identity:
        failures.append("commissioning_sensor_replaced")
    if current_configuration_sha256 != record.configuration_sha256:
        failures.append("commissioning_configuration_changed")
    if current_mounting_or_pose != record.mounting_or_pose:
        failures.append("commissioning_mounting_changed")
    if current_model_profile_id not in record.compatible_model_profile_ids:
        failures.append("commissioning_model_profile_incompatible")
    if not record.baseline_noise_summary:
        failures.append("commissioning_baseline_noise_missing")
    if signal_chain_report.get("compatibility_passed") is not True:
        failures.append("signal_chain_not_compatible")
    fixture_only = signal_chain_report.get("physical_source_proven") is not True
    site_verified_claim_allowed = not failures and not fixture_only and signal_chain_report.get("quality_passed") is True
    body = {
        "schema": "sentinel-edge-site-commissioning-evaluation/1.0",
        "commissioning_id": record.commissioning_id,
        "record_sha256": signed.record_sha256,
        "site_id": record.site_id,
        "calibration_identity": record.calibration_identity,
        "signal_chain_profile_sha256": record.signal_chain_profile_sha256,
        "site_verified_claim_allowed": site_verified_claim_allowed,
        "review_or_degraded_only": not site_verified_claim_allowed,
        "state": CapabilityState.FIELD_QUALIFIED.value if site_verified_claim_allowed else CapabilityState.TESTED.value if not failures else CapabilityState.FAILED.value,
        "failures": sorted(set(failures)),
        "limitations": ["fixture_signal_not_site_verification"] if fixture_only else [],
        "evaluated_at": now.isoformat(),
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}


def write_signal_chain_report(path: str | Path, report: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
