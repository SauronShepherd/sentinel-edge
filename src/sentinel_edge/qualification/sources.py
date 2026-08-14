from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

from sentinel_edge.domain.models import CapabilityState, SourceDecisionState, SourceMode, SourceObservationEvidence, SourcePolicyManifest, SourceQualificationReport
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


def validate_canonical_source_link(url: str, *, historical: bool = False) -> tuple[bool, tuple[str, ...]]:
    """Release-lint a source reference without performing network resolution."""
    normalized = url.strip()
    reasons: list[str] = []
    if not normalized.startswith("https://"):
        reasons.append("canonical_source_https_required")
    authority_and_path = normalized.removeprefix("https://") if normalized.startswith("https://") else ""
    authority = authority_and_path.split("/", 1)[0].split("?", 1)[0]
    if not authority or "@" in authority or "://" in authority:
        reasons.append("canonical_source_authority_invalid")
    if "#" in normalized:
        reasons.append("canonical_source_fragment_not_allowed")
    if historical:
        reasons.append("source_reference_historical_only")
    return not reasons, tuple(reasons or ("canonical_source_link_valid",))


def load_source_policy(path:str|Path)->SourcePolicyManifest:
    return SourcePolicyManifest.model_validate_json(Path(path).read_text(encoding='utf-8'))

def load_source_observation(path:str|Path)->SourceObservationEvidence:
    return SourceObservationEvidence.model_validate_json(Path(path).read_text(encoding='utf-8'))

def qualify_source(policy:SourcePolicyManifest, observation:SourceObservationEvidence, *, now:datetime|None=None)->SourceQualificationReport:
    now=now or datetime.now(timezone.utc); reasons=[]
    if observation.source_id!=policy.source_id: reasons.append('source_identity_mismatch')
    reach=observation.reachable
    authorized=(policy.source_mode in {SourceMode.FIXTURE,SourceMode.SIMULATED}) or (observation.authenticated and policy.entitlement=='authorized')
    rights=policy.rights_permission in {'retain_bytes','derived_only','reference_only','public_domain','licensed'}
    schema=observation.schema_version==policy.expected_schema_version
    terms=observation.terms_revision==policy.terms_revision and observation.license_id==policy.license_id and now<policy.review_at and now<policy.expires_at
    age=max(0.0,(observation.observed_at-observation.source_event_at).total_seconds()); fresh=age<=policy.freshness_max_age_seconds
    generation=(not policy.snapshot_generation_required) or bool(observation.generation_id)
    cache_ok=(not policy.authenticated_cache) or bool(observation.cache_context_sha256 and observation.authorization_scope_sha256)
    fit=policy.provider_maturity in {'fixture','stable','ga','official'} and bool(policy.owner.strip()) and bool(policy.canonical_url.strip()) and bool(policy.account_availability.strip()) and bool(policy.support_assumptions.strip()) and policy.failure_behavior in {'disable_influence','stale_context','fixture_only','reference_only'}
    for ok,code in [(reach,'endpoint_unreachable'),(authorized,'provider_not_authorized'),(rights,'rights_not_permitted'),(schema,'schema_incompatible'),(terms,'terms_or_review_expired'),(fresh,'source_stale'),(generation,'generation_evidence_missing'),(cache_ok,'authenticated_cache_context_missing'),(fit,'failure_behavior_invalid')]:
        if not ok: reasons.append(code)
    influence=policy.enabled and reach and authorized and rights and schema and terms and fresh and generation and cache_ok and fit
    release_ready=influence and policy.source_mode is SourceMode.LIVE
    state=CapabilityState.TARGET_QUALIFIED if release_ready else CapabilityState.TESTED if influence else CapabilityState.EXPIRED if not terms else CapabilityState.FAILED
    decision_state = SourceDecisionState.ACTIVE if influence else SourceDecisionState.REVIEW_REQUIRED if not terms or not schema or not rights or not authorized else SourceDecisionState.DISABLED
    return SourceQualificationReport(source_id=policy.source_id, attribution=policy.owner, license_id=policy.license_id, canonical_url=policy.canonical_url, state=state,decision_state=decision_state,endpoint_reachable=reach,provider_authorized=authorized,rights_permitted=rights,schema_compatible=schema,terms_current=terms,freshness_valid=fresh,generation_consistent=generation and cache_ok,product_fit=fit,decision_influence_allowed=influence,release_ready=release_ready,policy_sha256=sha256_bytes(canonical_json_bytes(policy.model_dump(mode='json'))),observation_sha256=sha256_bytes(canonical_json_bytes(observation.model_dump(mode='json'))),reason_codes=tuple(sorted(set(reasons))) if reasons else ('source_release_ready' if release_ready else 'source_fixture_qualified',))

def summarize_sources(reports:list[SourceQualificationReport])->dict:
    enabled=len(reports); live_ready=sum(r.release_ready for r in reports); influence=sum(r.decision_influence_allowed for r in reports)
    return {'schema':'sentinel-edge-source-readiness/1.0','enabled_count':enabled,'decision_influence_count':influence,'live_release_ready_count':live_ready,'all_enabled_sources_qualified':all(r.decision_influence_allowed for r in reports),'h0_zero_live_source_valid':enabled==0 or all(r.decision_influence_allowed for r in reports),'reports':[r.model_dump(mode='json') for r in reports]}
