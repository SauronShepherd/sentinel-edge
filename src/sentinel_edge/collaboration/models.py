"""Deterministic, privacy-minimized collaborative signal contracts."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Hazard = Literal["wildfire", "earthquake", "flood", "landslide"]
DomainKind = Literal["spatial_cell", "observation_area", "camera_sector", "river_reach", "catchment", "slope", "monitored_site", "unknown"]
OBSERVATIONS = {"wildfire": {"possible_smoke", "persistent_smoke", "review_required", "smoke_observation_resolved"}, "earthquake": {"local_trigger", "earthquake_like_signal", "shaking_ended"}, "flood": {"rainfall_elevated", "water_rising", "threshold_approaching", "threshold_exceeded", "flooding_observed", "falling"}, "landslide": {"saturation_rising", "movement_anomaly", "review_required", "movement_observation_resolved"}}
ALLOWED_DOMAIN_KINDS = {
    "earthquake": {"spatial_cell"},
    "wildfire": {"observation_area", "camera_sector"},
    "flood": {"river_reach", "catchment"},
    "landslide": {"slope", "monitored_site"},
}

class CorrelationDomain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: DomainKind
    id: str = Field(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9._:-]+$")
    domain_policy_id: str | None = Field(default=None, max_length=96, pattern=r"^[A-Za-z0-9._:-]+$")

class CollaborativeSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    signal_id: str = Field(min_length=16, max_length=80)
    episode_id: str = Field(min_length=16, max_length=80)
    sequence: int = Field(ge=0)
    node_pseudonym: str = Field(min_length=16, max_length=96, pattern=r"^[A-Za-z0-9_-]+$")
    hazard: Hazard
    observation: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    correlation_domain: CorrelationDomain
    event_time_bucket: datetime
    confidence_band: Literal["low", "medium", "high", "unknown"]
    coverage_band: Literal["good", "partial", "degraded", "blind", "unknown"]
    sensor_health: Literal["healthy", "degraded", "failed", "unknown"]
    clock_uncertainty_band: Literal["low", "medium", "high", "unknown"]
    source_mode: Literal["live", "fixture", "simulated", "replayed"]
    sharing_policy_version: str = Field(min_length=1, max_length=32)
    research_use_allowed: bool
    expires_at: datetime
    reason_codes: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def validate_observation(self) -> "CollaborativeSignal":
        if self.observation not in OBSERVATIONS[self.hazard]:
            raise ValueError("UNSUPPORTED_OBSERVATION")
        return self

class CollaborationConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sharing_enabled: bool = False
    research_enabled: bool = False
    hazards: dict[Hazard, bool]
    policy_version: str = Field(min_length=1, max_length=32)
    updated_at: datetime

    @model_validator(mode="after")
    def validate_research_requires_sharing(self) -> "CollaborationConsent":
        if self.research_enabled and not self.sharing_enabled:
            raise ValueError("RESEARCH_REQUIRES_SHARING")
        return self


class CollaborativeSignalEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    envelope_version: Literal["1.0"] = "1.0"
    received_at: datetime
    transport: Literal["fixture", "email", "future_http", "future_zenoh"]
    transport_message_id: str = Field(min_length=1, max_length=160)
    transport_trust: Literal["fixture_qualified", "email_unverified", "authenticated_peer", "rejected"]
    signal: CollaborativeSignal
    validation_state: Literal["admitted", "context_only", "rejected"]
    validation_reason_codes: list[str] = Field(default_factory=list, max_length=16)
    correlation_id: str = Field(min_length=8, max_length=96)


class CorrelationDecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_id: str = Field(min_length=8, max_length=96)
    policy_id: str = Field(min_length=1, max_length=96)
    hazard: Hazard
    domain_kind: DomainKind
    domain_id: str = Field(min_length=1, max_length=96)
    window_start: datetime
    window_end: datetime
    candidate_signal_ids: list[str]
    accepted_signal_ids: list[str]
    rejected_signal_ids: list[str]
    independent_peer_count: int = Field(ge=0)
    selected_action: Literal["no_action", "context_only", "create_review_incident", "update_incident", "multi_node_trigger_simulated"]
    positive_reasons: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    created_or_updated_incident_id: str | None = None
    created_at: datetime
