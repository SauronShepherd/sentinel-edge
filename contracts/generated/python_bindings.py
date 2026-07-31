# generated; do not edit
from dataclasses import dataclass

@dataclass(frozen=True)
class AnalyzerV1:
    bundle_id: str
    inputs: tuple[object, ...]
    limitations: tuple[object, ...]
    source_spans: tuple[object, ...]
    claims: tuple[object, ...]
    media_records: tuple[object, ...]
    derivation: dict[str, object]
    trust_factors: dict[str, object]

@dataclass(frozen=True)
class ApiV1:
    resource: str
    pagination: dict[str, object]
    cursor: str
    audit_context: dict[str, object]
    errors: tuple[object, ...]

@dataclass(frozen=True)
class CollectorV1:
    observation_id: str
    observed_at: str
    clock_quality: dict[str, object]
    replay: bool
    units: str
    source_health: dict[str, object]
    acquisition_audit: dict[str, object]
    policy: dict[str, object]

@dataclass(frozen=True)
class IncidentV1:
    incident_id: str
    expected_version: int
    projection_version: int
    inputs: tuple[object, ...]
    commands: tuple[object, ...]
    transitions: tuple[object, ...]
    reviews: tuple[object, ...]
    effects: tuple[object, ...]

@dataclass(frozen=True)
class RuntimeV1:
    job_id: str
    model_hash: str
    profile_hash: str
    deterministic: bool
    abstained: bool
    results: tuple[object, ...]
    hazard_inference: dict[str, object]
    lifecycle: dict[str, object]
    health: dict[str, object]
    benchmark_samples: tuple[object, ...]

