from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import IntEnum, StrEnum
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HazardKind(StrEnum):
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    LANDSLIDE = "landslide"


class SourceDecisionState(StrEnum):
    ACTIVE = "active"
    REVIEW_REQUIRED = "review_required"
    DISABLED = "disabled"


class SourceMode(StrEnum):
    LIVE = "live"
    CACHED = "cached"
    SIMULATED = "simulated"
    FIXTURE = "fixture"
    REPLAYED = "replayed"


class ContentOrigin(StrEnum):
    """Provenance label for content shown to an operator or exported."""

    SOURCE = "source"
    OPERATOR = "operator"
    DETERMINISTIC_TRANSFORM = "deterministic_transform"
    ANALYTICAL_MODEL = "analytical_model"
    GENERATIVE_MODEL = "generative_model"
    UNKNOWN = "unknown"




class MeasurementQuality(StrEnum):
    VALID = "valid"
    SUSPECT = "suspect"
    INVALID = "invalid"
    MISSING = "missing"


class MeasurementStatistic(StrEnum):
    INSTANTANEOUS = "instantaneous"
    RATE = "rate"
    ACCUMULATION = "accumulation"
    MEAN = "mean"
    RMS = "rms"
    CHANGE = "change"


class UncertaintyStatus(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class TimeOrigin(StrEnum):
    RTC = "rtc"
    MANUAL = "manual"
    GNSS = "gnss"
    NTP = "ntp"
    NTS = "nts"
    FIXTURE = "fixture"


class TimeTrustState(StrEnum):
    TRUSTED = "trusted"
    DISPLAY_ONLY = "display_only"
    DEGRADED = "degraded"
    UNUSABLE = "unusable"


class MeasurementValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observed_property_id: str
    value: float
    unit: str
    quality: MeasurementQuality = MeasurementQuality.VALID
    uncertainty: float | None = Field(default=None, ge=0.0)
    uncertainty_status: UncertaintyStatus = UncertaintyStatus.UNKNOWN
    phenomenon_start: datetime
    phenomenon_end: datetime
    statistic: MeasurementStatistic
    axis: str | None = None
    orientation: str | None = None
    reference: str | None = None
    source_value_key: str

    @model_validator(mode="after")
    def validate_measurement(self) -> "MeasurementValue":
        if self.phenomenon_end < self.phenomenon_start:
            raise ValueError("phenomenon_end cannot precede phenomenon_start")
        if self.uncertainty_status is UncertaintyStatus.KNOWN and self.uncertainty is None:
            raise ValueError("known uncertainty requires a numeric value")
        if self.uncertainty_status is not UncertaintyStatus.KNOWN and self.uncertainty is not None:
            raise ValueError("numeric uncertainty requires known uncertainty_status")
        if not self.observed_property_id.strip() or not self.unit.strip() or not self.source_value_key.strip():
            raise ValueError("measurement identifiers and unit must not be blank")
        return self


class TimeSourceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    origin: TimeOrigin
    authenticated: bool
    observed_utc: datetime
    observed_monotonic_ns: int = Field(ge=0)
    uncertainty_ms: float = Field(ge=0.0)
    age_ms: float = Field(ge=0.0)
    stratum: int | None = Field(default=None, ge=0, le=16)
    reference_id: str | None = None
    continuity_id: str
    clock_epoch: int = Field(default=0, ge=0)
    clock_uncertainty_ms: float = Field(default=0.0, ge=0.0)
    certificate_bootstrap_valid: bool | None = None

    @field_validator("source_id", "continuity_id")
    @classmethod
    def time_fields_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("time source fields must not be blank")
        return value


class TimeTrustSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: TimeTrustState
    selected_source_id: str | None
    selected_origin: TimeOrigin | None
    authenticated: bool
    uncertainty_ms: float | None
    clock_epoch: int = Field(ge=0)
    display_time_allowed: bool
    security_validity_allowed: bool
    remote_freshness_allowed: bool
    peer_correlation_allowed: bool
    reason_codes: tuple[str, ...] = ()
    sources: tuple[TimeSourceObservation, ...] = ()


class RuntimeMode(StrEnum):
    JUDGE = "judge"
    BENCHMARK = "benchmark"
    FIELD_LAB = "field_lab"
    DEVELOPMENT = "development"


class HealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALE = "stale"
    FAILED = "failed"
    UNKNOWN = "unknown"


class CoverageState(StrEnum):
    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    BLIND = "blind"


class IncidentState(StrEnum):
    NORMAL = "normal"
    WATCH = "watch"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    DEGRADED = "degraded"


class CriticalityTier(IntEnum):
    A_IMMEDIATE = 0
    B_URGENT = 1
    C_TIMELY = 2
    D_PERIODIC = 3
    E_BACKGROUND = 4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OpportunityDisposition(StrEnum):
    OFFERED = "offered"
    QUEUED = "queued"
    DEFERRED = "deferred"
    PROCESSED = "processed"
    SKIPPED = "skipped"
    REPLACED = "replaced"
    INVALID = "invalid"
    DROPPED = "dropped"
    EXPIRED = "expired"
    FAILED = "failed"
    DEADLINE_MISSED = "deadline_missed"


class ClaimClass(StrEnum):
    MEASURED = "measured"
    REPLAYED = "replayed"
    SIMULATED = "simulated"
    TARGET = "target"
    RESEARCH = "research"


class BenchmarkVariant(StrEnum):
    B0 = "B0"
    B1 = "B1"
    O1 = "O1"


class CapabilityState(StrEnum):
    SPECIFIED = "specified"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    TARGET_QUALIFIED = "target_qualified"
    RELEASE_ADMITTED = "release_admitted"
    FIELD_QUALIFIED = "field_qualified"
    DEFERRED = "deferred"
    BLOCKED = "blocked"
    FAILED = "failed"
    EXPIRED = "expired"


class ConfigurationState(StrEnum):
    STAGED = "staged"
    ACTIVE = "active"
    LAST_KNOWN_GOOD = "last_known_good"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class ReviewActionKind(StrEnum):
    ACKNOWLEDGE = "acknowledge"
    SNOOZE = "snooze"
    UNSNOOZE = "unsnooze"
    COMMENT = "comment"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"
    DEAD_LETTER = "dead_letter"


class AuthorityMutationKind(StrEnum):
    INCIDENT = "incident"
    REVIEW = "review"
    NOTIFICATION_INTENT = "notification_intent"
    NOTIFICATION_DELIVERY = "notification_delivery"
    CONFIGURATION = "configuration"
    COMMAND = "command"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    CLAIM_LINK = "claim_link"
    INCIDENT_RELATION = "incident_relation"
    EVIDENCE_LIFECYCLE = "evidence_lifecycle"
    MEDIA_PARSE = "media_parse"
    EVIDENCE_REEVALUATION = "evidence_reevaluation"
    DISPOSITION = "disposition"


class SourceStanding(StrEnum):
    OFFICIAL = "official"
    AUTHORITATIVE = "authoritative"
    FIRST_PARTY = "first_party"
    NEWS = "news"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class MediaIntegrityState(StrEnum):
    ORIGINAL_VERIFIED = "original_verified"
    DERIVATIVE = "derivative"
    MANIPULATION_SUSPECT = "manipulation_suspect"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ExtractionConfidenceState(StrEnum):
    VERIFIED = "verified"
    MODEL_ESTIMATE = "model_estimate"
    LOW = "low"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class EvidenceRetentionState(StrEnum):
    RETAINED = "retained"
    METADATA_ONLY = "metadata_only"
    REJECTED = "rejected"


class EvidenceRightsMode(StrEnum):
    RETAIN_BYTES = "retain_bytes"
    DERIVED_ONLY = "derived_only"
    REFERENCE_ONLY = "reference_only"


class EvidenceContentState(StrEnum):
    AVAILABLE = "available"
    METADATA_ONLY = "metadata_only"
    REDACTED = "redacted"
    EXPIRED = "expired"
    DELETED = "deleted"
    UNAVAILABLE_AT_CAPTURE = "unavailable_at_capture"
    MISSING_EXTERNAL = "missing_external"


class EvidenceLifecycleAction(StrEnum):
    REGISTER = "register"
    REDACT = "redact"
    EXPIRE = "expire"
    DELETE = "delete"
    MARK_EXTERNAL_MISSING = "mark_external_missing"


class MediaParserStatus(StrEnum):
    COMPLETED = "completed"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    FAILED = "failed"


class ParserIsolationState(StrEnum):
    NOT_REQUIRED = "not_required"
    SANDBOXED = "sandboxed"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


class ClaimEvidenceRelation(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SAME_FAMILY = "same_family"
    DERIVED_FROM = "derived_from"


class IncidentRelationKind(StrEnum):
    CASCADE_CONTEXT = "cascade_context"
    SUSCEPTIBILITY_INCREASE = "susceptibility_increase"
    TEMPORAL_ASSOCIATION = "temporal_association"
    SAME_EVENT_SOLUTION = "same_event_solution"
    MERGED_ALIAS = "merged_alias"


class IncidentIdentityOutcome(StrEnum):
    NEW = "new"
    DUPLICATE = "duplicate"


class IncidentCommandKind(StrEnum):
    CORROBORATE = "corroborate"
    CONTRADICT = "contradict"
    CONTROL = "control"
    RESOLVE = "resolve"
    REOPEN = "reopen"
    LINK = "link"
    MERGE = "merge"


class IncidentLabel(StrEnum):
    CONFIRM = "confirm"
    REJECT = "reject"
    UNCERTAIN = "uncertain"
    CONTROL = "control"


class PrincipalRole(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class CommandStatus(StrEnum):
    ACCEPTED = "accepted"
    VALIDATING = "validating"
    COMMITTED = "committed"
    PROJECTED = "projected"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    CONFLICT = "conflict"


_COMMAND_STATUS_TRANSITIONS: dict[CommandStatus, frozenset[CommandStatus]] = {
    CommandStatus.ACCEPTED: frozenset({CommandStatus.VALIDATING, CommandStatus.REJECTED, CommandStatus.EXPIRED, CommandStatus.SUPERSEDED}),
    CommandStatus.VALIDATING: frozenset({CommandStatus.COMMITTED, CommandStatus.REJECTED, CommandStatus.EXPIRED, CommandStatus.SUPERSEDED}),
    CommandStatus.COMMITTED: frozenset({CommandStatus.PROJECTED}),
    CommandStatus.PROJECTED: frozenset(),
    CommandStatus.REJECTED: frozenset(),
    CommandStatus.EXPIRED: frozenset(),
    CommandStatus.SUPERSEDED: frozenset(),
    CommandStatus.CONFLICT: frozenset(),
}


def validate_command_status_transition(previous: CommandStatus, current: CommandStatus) -> CommandStatus:
    if current not in _COMMAND_STATUS_TRANSITIONS[previous]:
        raise ValueError(f"illegal command lifecycle transition {previous.value}->{current.value}")
    return current


class UpdateBundleState(StrEnum):
    STAGED = "staged"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ACTIVATED = "activated"
    ROLLED_BACK = "rolled_back"


T = TypeVar("T")


class BoundaryEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_name: str
    schema_version: str = "1.0.0"
    message_id: UUID = Field(default_factory=uuid4)
    producer_component: str
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: T

    @field_validator("schema_name", "producer_component")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "2.0.0"
    observation_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    source_id: str
    hazard: HazardKind
    source_mode: SourceMode
    boot_id: str = "fixture-boot-1"
    sequence: int = Field(ge=0)
    observed_at: datetime
    received_at: datetime
    values: dict[str, float]
    units: dict[str, str]
    quality_flags: tuple[str, ...] = ()
    source_lineage: str = "fixture-v1"
    clock_epoch: int = Field(default=0, ge=0)
    clock_uncertainty_ms: float = Field(default=0.0, ge=0.0)
    measurements: tuple[MeasurementValue, ...] = ()
    measurement_references: dict[str, str] = Field(default_factory=dict)
    measurement_orientations: dict[str, str] = Field(default_factory=dict)
    measurement_uncertainty: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation(self) -> "Observation":
        if self.received_at < self.observed_at:
            raise ValueError("received_at cannot precede observed_at")
        if set(self.values) - set(self.units):
            raise ValueError("every value must have a unit")
        if any(not isinstance(value, (int, float)) for value in self.values.values()):
            raise ValueError("observation values must be numeric")
        if not self.boot_id.strip():
            raise ValueError("boot_id must not be blank")
        if self.measurements:
            keys = [item.source_value_key for item in self.measurements]
            if len(keys) != len(set(keys)):
                raise ValueError("measurement source_value_key values must be unique")
            if set(keys) != set(self.values):
                raise ValueError("measurements must cover exactly the observation values")
            for item in self.measurements:
                if self.units[item.source_value_key] != item.unit or self.values[item.source_value_key] != item.value:
                    raise ValueError("measurement values/units must match observation compatibility fields")
        else:
            generated = []
            invalid = {flag.split(":", 1)[1] for flag in self.quality_flags if flag.startswith("invalid:")}
            suspect = {flag.split(":", 1)[1] for flag in self.quality_flags if flag.startswith("suspect:")}
            for key, value in sorted(self.values.items()):
                if key in invalid:
                    quality = MeasurementQuality.INVALID
                elif key in suspect:
                    quality = MeasurementQuality.SUSPECT
                else:
                    quality = MeasurementQuality.VALID
                if key.endswith("_mm_h") or key.endswith("_m_per_h") or key.endswith("_deg_h"):
                    statistic = MeasurementStatistic.RATE
                    start = self.observed_at - timedelta(hours=1)
                elif "_1h_" in key:
                    statistic = MeasurementStatistic.ACCUMULATION
                    start = self.observed_at - timedelta(hours=1)
                elif "_6h_" in key:
                    statistic = MeasurementStatistic.ACCUMULATION
                    start = self.observed_at - timedelta(hours=6)
                elif "_24h_" in key:
                    statistic = MeasurementStatistic.ACCUMULATION
                    start = self.observed_at - timedelta(hours=24)
                elif key.endswith("_rms"):
                    statistic = MeasurementStatistic.RMS
                    start = self.observed_at
                else:
                    statistic = MeasurementStatistic.INSTANTANEOUS
                    start = self.observed_at
                axis = key.rsplit("_", 1)[-1] if key in {"accel_x", "accel_y", "accel_z"} else None
                orientation = self.measurement_orientations.get(key)
                if orientation is None and key.startswith("accel_"):
                    orientation = f"sensor-frame:{axis}:positive-source-declared"
                elif orientation is None and "tilt" in key:
                    orientation = "positive-source-declared"
                elif orientation is None and ("rate_of_rise" in key or "water_level" in key):
                    orientation = "positive-up"
                reference = self.measurement_references.get(key)
                if reference is None and key.startswith("accel_"):
                    reference = f"sensor-frame:{self.source_id}"
                elif reference is None and ("tilt" in key or "vibration" in key):
                    reference = f"sensor-frame:{self.source_id}"
                elif reference is None and ("water_level" in key or "rate_of_rise" in key or "elevation" in key or "depth" in key):
                    reference = f"local-datum-unqualified:{self.source_id}"
                uncertainty = self.measurement_uncertainty.get(key)
                generated.append(MeasurementValue(
                    observed_property_id=key, value=float(value), unit=self.units[key], quality=quality,
                    uncertainty=uncertainty,
                    uncertainty_status=UncertaintyStatus.KNOWN if uncertainty is not None else UncertaintyStatus.UNKNOWN,
                    phenomenon_start=start, phenomenon_end=self.observed_at, statistic=statistic,
                    axis=axis, orientation=orientation, reference=reference,
                    source_value_key=key,
                ))
            object.__setattr__(self, "measurements", tuple(generated))
        return self

    @property
    def capture_age_ms(self) -> float:
        return max(0.0, (self.received_at - self.observed_at).total_seconds() * 1000)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis_id: UUID = Field(default_factory=uuid4)
    observation_id: UUID
    correlation_id: UUID = Field(default_factory=uuid4)
    boot_id: str = "fixture-boot-1"
    source_mode: SourceMode = SourceMode.FIXTURE
    hazard: HazardKind
    score: float = Field(ge=0.0, le=1.0)
    state_hint: IncidentState
    features: dict[str, float]
    coverage: CoverageState
    abstained: bool = False
    reason_codes: tuple[str, ...] = ()
    model_profile_id: str = "deterministic-v1"
    source_lineage: str = "fixture-v1"
    config_hashes: tuple[str, ...] = ()
    incident_id_hint: UUID | None = None
    produced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_time: datetime | None = None


class WorkloadSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workload_id: str
    hazard: HazardKind
    tier: CriticalityTier
    period_ms: int = Field(gt=0)
    deadline_ms: int = Field(gt=0)
    max_deferral_ms: int = Field(ge=0)
    estimated_cost_ms: int = Field(gt=0)
    memory_mb: int = Field(gt=0)
    profile_id: str
    forced_scan_ms: int | None = Field(default=None, gt=0)


class ResourceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cpu_pressure: float = Field(ge=0.0, le=1.0)
    memory_pressure: float = Field(ge=0.0, le=1.0)
    io_pressure: float = Field(ge=0.0, le=1.0)
    temperature_c: float
    available_memory_mb: int = Field(ge=0)
    power_degraded: bool = False

    @property
    def overloaded(self) -> bool:
        return (
            self.cpu_pressure >= 0.90
            or self.memory_pressure >= 0.85
            or self.io_pressure >= 0.85
            or self.temperature_c >= 82.0
            or self.power_degraded
        )


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID = Field(default_factory=uuid4)
    opportunity_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    workload: WorkloadSpec
    released_at: datetime
    absolute_deadline: datetime
    released_monotonic_ns: int = Field(ge=0)
    deadline_monotonic_ns: int = Field(ge=0)
    payload: dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    deferral_count: int = 0
    reason_codes: list[str] = Field(default_factory=list)
    service_started_monotonic_ns: int | None = Field(default=None, ge=0)
    completed_monotonic_ns: int | None = Field(default=None, ge=0)


class OpportunityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    workload_id: str
    hazard: HazardKind
    scheduled_release_at: datetime
    actual_release_at: datetime | None = None
    captured_at: datetime | None = None
    queue_started_monotonic_ns: int | None = Field(default=None, ge=0)
    service_started_monotonic_ns: int | None = Field(default=None, ge=0)
    completed_monotonic_ns: int | None = Field(default=None, ge=0)
    deadline_monotonic_ns: int | None = Field(default=None, ge=0)
    disposition: OpportunityDisposition = OpportunityDisposition.OFFERED
    reason_codes: list[str] = Field(default_factory=list)


class SchedulerSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    active: tuple[str, ...]
    queued: tuple[str, ...]
    deferred: tuple[str, ...]
    sleeping: tuple[str, ...]
    overloaded: bool
    degradation_level: int = Field(ge=0)
    reason_codes: tuple[str, ...] = ()
    scheduling_policy: str = "normal"


class IncidentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    hazard: HazardKind
    state: IncidentState
    confidence: float = Field(ge=0.0, le=1.0)
    coverage: CoverageState
    source_mode: SourceMode = SourceMode.FIXTURE
    first_observed_at: datetime
    last_observed_at: datetime
    event_time_watermark: datetime | None = None
    version: int = Field(ge=1)
    reason_codes: tuple[str, ...] = ()
    analysis_ids: tuple[UUID, ...] = ()
    correlation_ids: tuple[UUID, ...] = ()
    last_boot_id: str = "fixture-boot-1"
    source_lineage: str = "fixture-v1"
    model_profile_id: str = "deterministic-v1"
    config_hashes: tuple[str, ...] = ()
    labels: tuple[IncidentLabel, ...] = ()


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    source_id: str
    source_standing: SourceStanding
    authority_role: str = "operational_source"
    media_integrity: MediaIntegrityState
    extraction_confidence_state: ExtractionConfidenceState
    extraction_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    freshness_state: HealthState
    claim_text: str
    content_sha256: str
    perceptual_hash: str | None = None
    origin_key: str
    family_id: str | None = None
    parent_evidence_id: UUID | None = None
    independent_origin_proven: bool = False
    retention_state: EvidenceRetentionState
    parser_state: ParserIsolationState
    rights_basis: str | None = None
    rights_mode: EvidenceRightsMode | None = None
    rights_expires_at: datetime | None = None
    modality: str = "metadata"
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason_codes: tuple[str, ...] = ()
    person_identification_performed: bool = False
    subject_ref: str | None = None
    processing_basis: str = "operational_non_consent"

    @model_validator(mode="after")
    def validate_evidence(self) -> "EvidenceItem":
        if not self.authority_role.strip():
            raise ValueError("authority_role must not be blank")
        for value in (self.source_id, self.claim_text, self.content_sha256, self.origin_key, self.modality):
            if not value.strip():
                raise ValueError("evidence identity and content fields must not be blank")
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.content_sha256.lower()):
            raise ValueError("content_sha256 must be a lowercase SHA-256 hex digest")
        if self.extraction_confidence_state in {ExtractionConfidenceState.VERIFIED, ExtractionConfidenceState.MODEL_ESTIMATE, ExtractionConfidenceState.LOW}:
            if self.extraction_confidence is None:
                raise ValueError("declared extraction confidence state requires a numeric confidence")
        elif self.extraction_confidence is not None:
            raise ValueError("unknown/not-applicable extraction confidence cannot carry a numeric value")
        if self.retention_state is EvidenceRetentionState.RETAINED and not (self.rights_basis and self.rights_basis.strip()):
            raise ValueError("retained evidence requires a rights_basis")
        derived_rights_mode = self.rights_mode
        if derived_rights_mode is None:
            if self.retention_state is EvidenceRetentionState.RETAINED:
                derived_rights_mode = EvidenceRightsMode.RETAIN_BYTES
            elif self.retention_state is EvidenceRetentionState.METADATA_ONLY:
                derived_rights_mode = EvidenceRightsMode.DERIVED_ONLY
            else:
                derived_rights_mode = EvidenceRightsMode.REFERENCE_ONLY
            object.__setattr__(self, "rights_mode", derived_rights_mode)
        if self.retention_state is EvidenceRetentionState.RETAINED and derived_rights_mode is not EvidenceRightsMode.RETAIN_BYTES:
            raise ValueError("retained evidence requires retain_bytes rights mode")
        if self.retention_state is EvidenceRetentionState.METADATA_ONLY and derived_rights_mode is EvidenceRightsMode.RETAIN_BYTES:
            raise ValueError("metadata-only evidence cannot retain source bytes")
        if self.retention_state is EvidenceRetentionState.REJECTED and derived_rights_mode is not EvidenceRightsMode.REFERENCE_ONLY:
            raise ValueError("rejected evidence must remain reference_only")
        if self.rights_expires_at is not None and self.rights_expires_at <= self.received_at:
            raise ValueError("rights_expires_at must be later than received_at")
        if self.retention_state is EvidenceRetentionState.REJECTED and self.parser_state is not ParserIsolationState.REJECTED:
            raise ValueError("rejected retention requires rejected parser state")
        if self.person_identification_performed:
            raise ValueError("face, speaker, or person re-identification is outside Sentinel Edge scope")
        if self.subject_ref is not None and not self.subject_ref.strip():
            raise ValueError("subject_ref must not be blank")
        if not self.processing_basis.strip():
            raise ValueError("processing_basis must not be blank")
        return self


class EvidenceLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lifecycle_event_id: UUID = Field(default_factory=uuid4)
    evidence_id: UUID
    incident_id: UUID
    action: EvidenceLifecycleAction
    from_state: EvidenceContentState | None
    to_state: EvidenceContentState
    expected_version: int = Field(ge=0)
    resulting_version: int = Field(ge=1)
    actor: str
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deletion_proof_sha256: str | None = None
    redaction_profile_id: str | None = None
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_lifecycle_event(self) -> "EvidenceLifecycleEvent":
        if not self.actor.strip() or not self.reason.strip():
            raise ValueError("evidence lifecycle event requires actor and reason")
        if self.resulting_version != self.expected_version + 1:
            raise ValueError("evidence lifecycle version must increment by one")
        if self.action is EvidenceLifecycleAction.DELETE and not self.deletion_proof_sha256:
            raise ValueError("deletion requires a proof digest")
        if self.deletion_proof_sha256 is not None and (
            len(self.deletion_proof_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.deletion_proof_sha256.lower())
        ):
            raise ValueError("deletion_proof_sha256 must be a lowercase SHA-256 digest")
        return self


class EvidenceLifecycleProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: UUID
    incident_id: UUID
    state: EvidenceContentState
    version: int = Field(ge=0)
    readable: bool
    claim_eligible: bool
    rights_active: bool
    deletion_proven: bool
    last_event_id: UUID | None = None
    updated_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()


class MediaParserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str = "bounded-image-parser-v1"
    maximum_input_bytes: int = Field(default=8 * 1024 * 1024, gt=0)
    maximum_output_bytes: int = Field(default=12 * 1024 * 1024, gt=0)
    maximum_pixels: int = Field(default=24_000_000, gt=0)
    timeout_seconds: float = Field(default=3.0, gt=0.0, le=30.0)
    memory_limit_mb: int = Field(default=1024, ge=256, le=4096)
    cpu_limit_seconds: int = Field(default=2, ge=1, le=30)
    allowed_media_types: tuple[str, ...] = ("image/jpeg", "image/png")


class MediaParserReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    parse_id: UUID = Field(default_factory=uuid4)
    profile_id: str
    status: MediaParserStatus
    parser_state: ParserIsolationState
    input_sha256: str
    input_bytes: int = Field(ge=0)
    media_type: str
    detected_media_type: str | None = None
    output_sha256: str | None = None
    output_bytes: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    source_format: str | None = None
    sanitized_format: str | None = None
    metadata_stripped: bool = False
    alpha_preserved: bool = False
    network_namespace_proven: bool = False
    filesystem_scope: str = "ephemeral_private_directory"
    release_eligible: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason_codes: tuple[str, ...] = ()



class EvidenceReevaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reevaluation_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    evidence_id: UUID
    trigger_action: EvidenceLifecycleAction
    status: str = "completed"
    decision: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_supporting_links: int = Field(ge=0)
    active_contradictory_links: int = Field(ge=0)
    invalidated_links: int = Field(ge=0)
    incident_state_mutated: bool = False
    reason_codes: tuple[str, ...] = ()

    @field_validator("status", "decision")
    @classmethod
    def reevaluation_fields_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reevaluation fields must not be blank")
        return value



class EvidenceFamilySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family_id: str
    incident_id: UUID
    evidence_ids: tuple[UUID, ...]
    origin_keys: tuple[str, ...]
    independence_units: int = Field(ge=1)
    exact_duplicates: int = Field(ge=0)
    near_duplicates: int = Field(ge=0)
    independent_origins: int = Field(ge=0)


class ClaimNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    statement: str
    origin: ContentOrigin = ContentOrigin.UNKNOWN
    lineage: tuple[str, ...] = ()
    model_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "open"
    reason_codes: tuple[str, ...] = ()

    @field_validator("statement", "status")
    @classmethod
    def claim_fields_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim fields must not be blank")
        return value

    @model_validator(mode="after")
    def generated_claim_requires_provenance(self) -> "ClaimNode":
        if self.origin in {ContentOrigin.ANALYTICAL_MODEL, ContentOrigin.GENERATIVE_MODEL}:
            if not self.model_id or not self.model_id.strip():
                raise ValueError("model-generated claim requires model_id")
            if not self.lineage:
                raise ValueError("model-generated claim requires lineage")
        return self


class ClaimEvidenceLink(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    link_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID
    evidence_id: UUID
    relation: ClaimEvidenceRelation
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason_codes: tuple[str, ...] = ()


class TrustDimensionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    source_standing_counts: dict[str, int]
    media_integrity_counts: dict[str, int]
    extraction_confidence_counts: dict[str, int]
    freshness_counts: dict[str, int]
    evidence_families: int = Field(ge=0)
    independence_units: int = Field(ge=0)
    supporting_links: int = Field(ge=0)
    contradictory_links: int = Field(ge=0)
    invalidated_links: int = Field(default=0, ge=0)
    unresolved_claims: int = Field(ge=0)
    formula_version: str = "sentinel-trust-factors-v1"
    summary_band: str
    reason_codes: tuple[str, ...] = ()


class IncidentRelation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    relation_id: UUID = Field(default_factory=uuid4)
    source_incident_id: UUID
    source_hazard: HazardKind
    target_incident_id: UUID
    target_hazard: HazardKind
    relation: IncidentRelationKind
    confidence: float = Field(ge=0.0, le=1.0)
    expected_source_version: int = Field(ge=1)
    expected_target_version: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    reason: str

    @model_validator(mode="after")
    def validate_relation(self) -> "IncidentRelation":
        if self.source_incident_id == self.target_incident_id:
            raise ValueError("incident relation must connect two distinct incidents")
        if not self.actor.strip() or not self.reason.strip():
            raise ValueError("incident relation requires actor and reason")
        if self.relation is not IncidentRelationKind.MERGED_ALIAS and self.source_hazard is self.target_hazard:
            raise ValueError("same-hazard relation is allowed only for merged_alias")
        return self


class IncidentStatusCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    command_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    command: IncidentCommandKind
    expected_version: int = Field(ge=1)
    actor: str
    reason: str
    related_incident_id: UUID | None = None
    related_hazard: HazardKind | None = None
    idempotency_key: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_incident_command(self) -> "IncidentStatusCommand":
        if not self.actor.strip() or not self.reason.strip() or not self.idempotency_key.strip():
            raise ValueError("incident command fields must not be blank")
        if self.command in {IncidentCommandKind.LINK, IncidentCommandKind.MERGE}:
            if self.related_incident_id is None or self.related_hazard is None:
                raise ValueError("link/merge command requires a related incident")
        elif self.related_incident_id is not None or self.related_hazard is not None:
            raise ValueError("related incident is valid only for link/merge commands")
        return self


class IncidentCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: UUID = Field(default_factory=uuid4)
    hazard: HazardKind
    observed_at: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    horizontal_uncertainty_m: float = Field(default=0.0, ge=0.0)
    temporal_window_seconds: float = Field(default=300.0, gt=0.0)
    spatial_window_m: float = Field(default=1000.0, gt=0.0)
    source_id: str
    source_event_id: str | None = None

    @field_validator("source_id")
    @classmethod
    def candidate_source_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_id must not be blank")
        return value


class IncidentIdentityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    incident_id: UUID
    outcome: IncidentIdentityOutcome
    matched_candidate_id: UUID | None = None
    separation_m: float | None = Field(default=None, ge=0.0)
    time_delta_seconds: float | None = Field(default=None, ge=0.0)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason_codes: tuple[str, ...] = ()


class SourceHealth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    state: HealthState
    boot_id: str | None = None
    clock_epoch: int | None = None
    last_sequence: int | None = None
    last_observed_at: datetime | None = None
    event_time_watermark: datetime | None = None
    clock_uncertainty_ms: float = Field(default=0.0, ge=0.0)
    reason_codes: tuple[str, ...] = ()


class CapabilityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    capability_id: str
    state: HealthState
    consequence: str
    reason_codes: tuple[str, ...] = ()


class ClaimRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    claim_class: ClaimClass
    statement: str
    artifact_refs: tuple[str, ...]
    capability_hashes: tuple[str, ...] = ()
    config_hashes: tuple[str, ...] = ()
    model_hashes: tuple[str, ...] = ()
    release_candidate_id: str | None = None


class ConfigurationBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    bundle_id: str
    version: str
    actor: str
    workloads: tuple[WorkloadSpec, ...]
    settings: dict[str, Any] = Field(default_factory=dict)
    model_hashes: dict[str, str] = Field(default_factory=dict)
    source_hashes: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_bundle(self) -> "ConfigurationBundle":
        if self.schema_version != "1.0.0":
            raise ValueError("unsupported configuration schema_version")
        if not self.bundle_id.strip() or not self.version.strip() or not self.actor.strip():
            raise ValueError("bundle_id, version, and actor must not be blank")
        ids = [item.workload_id for item in self.workloads]
        if len(ids) != len(set(ids)):
            raise ValueError("workload identifiers must be unique")
        if not self.workloads:
            raise ValueError("at least one workload is required")
        return self


class ConfigurationActivationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    activation_id: UUID = Field(default_factory=uuid4)
    bundle_id: str
    version: str
    state: ConfigurationState
    actor: str
    bundle_sha256: str
    diff_sha256: str
    previous_bundle_id: str | None = None
    reason_codes: tuple[str, ...] = ()
    activated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    review_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    action: ReviewActionKind
    actor: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    snooze_until: datetime | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def validate_review(self) -> "ReviewAction":
        if not self.actor.strip():
            raise ValueError("actor must not be blank")
        if self.action is ReviewActionKind.SNOOZE:
            if self.snooze_until is None or self.snooze_until <= self.created_at:
                raise ValueError("snooze_until must be after created_at")
        elif self.snooze_until is not None:
            raise ValueError("snooze_until is only valid for snooze actions")
        if self.action is ReviewActionKind.COMMENT and not (self.comment and self.comment.strip()):
            raise ValueError("comment action requires text")
        return self


class IncidentReviewState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    snoozed_until: datetime | None = None
    snoozed_by: str | None = None
    review_count: int = Field(default=0, ge=0)


class NotificationIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    notification_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    incident_version: int = Field(ge=1)
    incident_state: IncidentState
    idempotency_key: str
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1, le=20)
    last_error: str | None = None
    receipt_id: str | None = None
    reason_codes: tuple[str, ...] = ()

    @field_validator("idempotency_key")
    @classmethod
    def key_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency_key must not be blank")
        return value


class AuthorityMutation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    position: int = Field(ge=1)
    kind: AuthorityMutationKind
    entity_id: str
    accepted_at: datetime
    payload: dict[str, Any]


class SourceHealthEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    source_id: str
    previous_state: HealthState | None = None
    state: HealthState
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    boot_id: str | None = None
    sequence: int | None = Field(default=None, ge=0)
    clock_uncertainty_ms: float = Field(default=0.0, ge=0.0)
    reason_codes: tuple[str, ...] = ()


class PrincipalRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    principal_id: str
    roles: tuple[PrincipalRole, ...]
    scopes: tuple[str, ...] = ()
    authentication_method: str = "local_bearer"
    principal_kind: Literal["human", "service", "device", "system"] = "human"
    session_epoch: int = Field(default=1, ge=1)
    device_trust_epoch: int = Field(default=1, ge=1)

    @field_validator("principal_id", "authentication_method")
    @classmethod
    def principal_fields_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("principal fields must not be blank")
        return value


class AuthorizationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: UUID = Field(default_factory=uuid4)
    principal: PrincipalRef
    operation: str
    target: str
    payload_sha256: str
    policy_version: str
    canonical_encoding_version: str = "sentinel-cjson-v1"
    accepted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    authorization_tag: str

    @model_validator(mode="after")
    def validate_decision(self) -> "AuthorizationDecision":
        if self.expires_at <= self.accepted_at:
            raise ValueError("authorization decision must expire after acceptance")
        if not self.operation.strip() or not self.target.strip() or not self.policy_version.strip():
            raise ValueError("authorization decision fields must not be blank")
        return self


class ClientAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    idempotency_key: str

    @field_validator("idempotency_key")
    @classmethod
    def acknowledge_key_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency_key must not be blank")
        return value


class ClientSnoozeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    until: datetime
    idempotency_key: str

    @field_validator("idempotency_key")
    @classmethod
    def snooze_key_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency_key must not be blank")
        return value


class AuthorizedReviewCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    command_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    action: ReviewActionKind
    snooze_until: datetime | None = None
    comment: str | None = None
    idempotency_key: str
    authorization: AuthorizationDecision
    payload_sha256: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_authorized_review(self) -> "AuthorizedReviewCommand":
        if self.payload_sha256 != self.authorization.payload_sha256:
            raise ValueError("authorization payload digest mismatch")
        if self.action is ReviewActionKind.SNOOZE and self.snooze_until is None:
            raise ValueError("snooze command requires snooze_until")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be blank")
        return self


class CommandReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    command_id: UUID
    principal_id: str
    operation: str
    target: str
    scoped_idempotency_key: str
    payload_sha256: str
    status: CommandStatus
    accepted_at: datetime
    committed_at: datetime | None = None
    result_version: int | None = Field(default=None, ge=1)
    result_sha256: str | None = None
    reason_codes: tuple[str, ...] = ()


class OfflineUpdateTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    length: int = Field(ge=0)
    sha256: str

    @field_validator("path")
    @classmethod
    def safe_relative_target_path(cls, value: str) -> str:
        candidate = value.strip().replace("\\", "/")
        if not candidate or candidate.startswith("/") or ".." in candidate.split("/"):
            raise ValueError("update target path must be a safe relative path")
        return candidate


class OfflineUpdateMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    bundle_id: str
    version: int = Field(ge=1)
    created_at: datetime
    expires_at: datetime
    compatible_project: str = "sentinel-edge"
    compatible_min_version: str
    compatible_max_version: str
    targets: tuple[OfflineUpdateTarget, ...]
    root_key_id: str
    minimum_tombstone_authority_position: int = Field(default=0, ge=0)
    required_tombstone_journal_sha256: str | None = None

    @model_validator(mode="after")
    def validate_update_metadata(self) -> "OfflineUpdateMetadata":
        if self.expires_at <= self.created_at:
            raise ValueError("update metadata expiry must follow creation")
        if not self.targets:
            raise ValueError("update bundle requires at least one target")
        if self.required_tombstone_journal_sha256 is not None and (
            len(self.required_tombstone_journal_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.required_tombstone_journal_sha256.lower())
        ):
            raise ValueError("required_tombstone_journal_sha256 must be a lowercase SHA-256 digest")
        paths = [item.path for item in self.targets]
        if len(paths) != len(set(paths)):
            raise ValueError("update target paths must be unique")
        return self


class OfflineUpdateVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_id: str
    version: int
    state: UpdateBundleState
    verified_at: datetime
    metadata_sha256: str
    signer_key_id: str
    reason_codes: tuple[str, ...] = ()


class SensorKind(StrEnum):
    IMU = "imu"
    CAMERA = "camera"


class HostObservation(BaseModel):
    """Observed host facts. Observation is not qualification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    system: str
    machine: str
    kernel_release: str
    os_id: str | None = None
    os_version_id: str | None = None
    board_model: str | None = None
    cpu_model: str | None = None
    cpu_count: int = Field(ge=1)
    memory_mb: int = Field(ge=0)
    architecture_64bit: bool
    psi_available: bool
    cgroup_v2: bool
    thermal_sensor_count: int = Field(ge=0)
    maximum_temperature_c: float | None = None
    power_evidence: str
    boot_id_sha256: str | None = None
    observed_files: dict[str, str] = Field(default_factory=dict)


class HostQualificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    report_id: UUID = Field(default_factory=uuid4)
    profile_id: str
    profile_sha256: str
    observation_sha256: str
    state: CapabilityState
    host_profile_match: bool
    target_device_claim_allowed: bool
    benchmark_claim_allowed: bool
    reason_codes: tuple[str, ...]
    observation: HostObservation
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImuSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=0)
    monotonic_ns: int = Field(ge=0)
    x: float
    y: float
    z: float
    unit: str


class SensorCommissioningReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    session_id: UUID = Field(default_factory=uuid4)
    sensor_kind: SensorKind
    source_id: str
    source_path: str
    source_sha256: str
    physical_source_proven: bool
    state: CapabilityState
    sample_count: int = Field(ge=0)
    duration_seconds: float = Field(ge=0.0)
    requested_rate_hz: float = Field(gt=0.0)
    observed_rate_hz: float = Field(ge=0.0)
    rate_error_fraction: float = Field(ge=0.0)
    maximum_gap_ms: float = Field(ge=0.0)
    p99_interval_jitter_ms: float = Field(ge=0.0)
    non_monotonic_samples: int = Field(ge=0)
    sequence_gaps: int = Field(ge=0)
    saturation_samples: int = Field(ge=0)
    required_axes: tuple[str, ...] = ("x", "y", "z")
    observed_unit: str | None = None
    reason_codes: tuple[str, ...]
    commissioned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    path: str
    sha256: str


class RuntimeProfileManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    profile_id: str
    workload_id: str
    hazard: HazardKind
    model_path: str
    model_sha256: str
    model_format: str
    runtime_name: str
    runtime_version: str
    execution_provider: str
    quantization: str
    thread_count: int = Field(gt=0)
    input_contract: dict[str, Any]
    output_contract: dict[str, Any]
    host_report_sha256: str | None = None
    quality_evidence: tuple[EvidenceBinding, ...] = ()
    benchmark_evidence: tuple[EvidenceBinding, ...] = ()
    created_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_runtime_profile(self) -> "RuntimeProfileManifest":
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        for value in (
            self.profile_id,
            self.workload_id,
            self.model_path,
            self.model_sha256,
            self.model_format,
            self.runtime_name,
            self.runtime_version,
            self.execution_provider,
            self.quantization,
        ):
            if not value.strip():
                raise ValueError("runtime profile string fields must not be blank")
        return self


class RuntimeProfileQualification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    profile_id: str
    manifest_sha256: str
    model_sha256: str
    state: CapabilityState
    runtime_identity_match: bool
    model_integrity_match: bool
    host_binding_match: bool
    quality_evidence_complete: bool
    benchmark_evidence_complete: bool
    target_qualified: bool
    release_admissible: bool
    reason_codes: tuple[str, ...]
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenchmarkEvidenceReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    benchmark_id: str
    benchmark_manifest_sha256: str
    host_report_sha256: str
    runtime_profile_sha256s: tuple[str, ...]
    source_class: ClaimClass
    variants: tuple[BenchmarkVariant, ...]
    raw_sample_count: int = Field(ge=0)
    opportunity_manifest_equal: bool
    quality_guardrails_passed: bool
    thermal_valid: bool
    power_valid: bool
    target_host_qualified: bool
    target_measurement_claim_allowed: bool
    reason_codes: tuple[str, ...]
    evidence_sha256: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CameraFrameSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=0)
    monotonic_ns: int = Field(ge=0)
    captured_at: datetime
    received_at: datetime
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    luminance_mean: float = Field(ge=0.0, le=255.0)
    blur_score: float = Field(ge=0.0)
    occlusion_fraction: float = Field(ge=0.0, le=1.0)
    frame_sha256: str


class CameraCommissioningReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    session_id: UUID = Field(default_factory=uuid4)
    sensor_kind: SensorKind = SensorKind.CAMERA
    source_id: str
    source_path: str
    source_sha256: str
    physical_source_proven: bool
    state: CapabilityState
    frame_count: int = Field(ge=0)
    duration_seconds: float = Field(ge=0.0)
    requested_fps: float = Field(gt=0.0)
    observed_fps: float = Field(ge=0.0)
    rate_error_fraction: float = Field(ge=0.0)
    maximum_gap_ms: float = Field(ge=0.0)
    p99_interval_jitter_ms: float = Field(ge=0.0)
    p95_capture_age_ms: float = Field(ge=0.0)
    non_monotonic_frames: int = Field(ge=0)
    sequence_gaps: int = Field(ge=0)
    frozen_frames: int = Field(ge=0)
    dark_frames: int = Field(ge=0)
    blurred_frames: int = Field(ge=0)
    occluded_frames: int = Field(ge=0)
    resolution_consistent: bool
    preprocessing_profile_sha256: str
    reason_codes: tuple[str, ...]
    commissioned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModelQualityManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    model_id: str
    hazard: HazardKind
    model_path: str
    model_sha256: str
    model_format: str
    license_id: str
    dataset_path: str
    dataset_sha256: str
    known_answer_path: str
    known_answer_sha256: str
    source_class: ClaimClass
    final_claim_set_frozen: bool
    split_group_field: str = "group_id"
    minimum_recall: float = Field(ge=0.0, le=1.0)
    maximum_false_alarm_rate: float = Field(ge=0.0, le=1.0)
    maximum_abstention_rate: float = Field(ge=0.0, le=1.0)
    score_tolerance: float = Field(ge=0.0)
    created_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_model_quality_manifest(self) -> "ModelQualityManifest":
        if self.expires_at <= self.created_at:
            raise ValueError("model quality manifest must expire after creation")
        return self


class ModelQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    model_id: str
    manifest_sha256: str
    model_integrity_match: bool
    dataset_integrity_match: bool
    known_answer_integrity_match: bool
    graph_quarantine_passed: bool
    known_answer_passed: bool
    split_leakage_detected: bool
    final_claim_set_frozen: bool
    sample_count: int = Field(ge=0)
    claim_sample_count: int = Field(ge=0)
    recall: float = Field(ge=0.0, le=1.0)
    false_alarm_rate: float = Field(ge=0.0, le=1.0)
    abstention_rate: float = Field(ge=0.0, le=1.0)
    quality_guardrails_passed: bool
    target_qualified: bool
    state: CapabilityState
    reason_codes: tuple[str, ...]
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourcePolicyManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    source_id: str
    enabled: bool
    source_mode: SourceMode
    owner: str
    canonical_url: str
    authority_role: str
    endpoint: str | None = None
    provider_maturity: str
    access_plan: str
    account_availability: str
    region: str | None = None
    entitlement: str
    rights_permission: str
    terms_revision: str
    license_id: str
    expected_schema_version: str
    freshness_max_age_seconds: int = Field(gt=0)
    review_at: datetime
    expires_at: datetime
    authenticated_cache: bool = False
    snapshot_generation_required: bool = False
    support_assumptions: str
    failure_behavior: str


class SourceObservationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    observed_at: datetime
    source_event_at: datetime
    reachable: bool
    authenticated: bool
    authorization_scope_sha256: str | None = None
    schema_version: str
    terms_revision: str
    license_id: str
    generation_id: str | None = None
    cache_context_sha256: str | None = None


class SourceQualificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    source_id: str
    attribution: str
    license_id: str
    canonical_url: str
    state: CapabilityState
    decision_state: SourceDecisionState
    endpoint_reachable: bool
    provider_authorized: bool
    rights_permitted: bool
    schema_compatible: bool
    terms_current: bool
    freshness_valid: bool
    generation_consistent: bool
    product_fit: bool
    decision_influence_allowed: bool
    release_ready: bool
    policy_sha256: str
    observation_sha256: str
    reason_codes: tuple[str, ...]
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReadinessState(StrEnum):
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class ReadinessReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    state: ReadinessState
    mode: RuntimeMode
    checks: dict[str, bool]
    reason_codes: tuple[str, ...]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
