"""Hazard-specific collaboration correlation policy.

This module belongs to the Component-4 collaboration slice.  It deliberately
keeps transport trust separate from hazard truth: fixture-qualified peers can
demonstrate a simulated earthquake multi-node trigger, while ordinary email
peers can only produce a review-level lead.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal
import hashlib

import yaml

from .models import ALLOWED_DOMAIN_KINDS, CollaborativeSignal, CorrelationDecisionRecord

CLOCK_RANK = {"low": 0, "medium": 1, "high": 2, "unknown": 3}
Action = Literal["no_action", "context_only", "create_review_incident", "update_incident", "multi_node_trigger_simulated"]


@dataclass(frozen=True)
class HazardCorrelationPolicy:
    hazard: str
    domain_kinds: frozenset[str]
    window_seconds: int
    min_independent_peers: int
    allowed_observations: frozenset[str]
    email_unverified_action: Action
    fixture_qualified_action: Action
    require_clock_band_at_most: str | None = None


@dataclass(frozen=True)
class CollaborationPolicy:
    policy_version: str
    hazards: dict[str, HazardCorrelationPolicy]


@dataclass(frozen=True)
class CorrelationDecision:
    """Compatibility projection used by the existing demo/tests."""

    action: str
    reason_codes: tuple[str, ...]
    independent_peer_count: int
    transport_trust: str


def load_policy(path: str | Path = "architecture/collaboration-policy.yaml") -> CollaborationPolicy:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if raw.get("schema") != "sentinel-edge.collaboration-policy.v1":
        raise ValueError("COLLABORATION_POLICY_SCHEMA_UNSUPPORTED")
    hazards_raw = raw.get("hazards")
    if not isinstance(hazards_raw, dict):
        raise ValueError("COLLABORATION_POLICY_HAZARDS_MISSING")
    hazards: dict[str, HazardCorrelationPolicy] = {}
    for hazard, value in hazards_raw.items():
        if hazard not in ALLOWED_DOMAIN_KINDS or not isinstance(value, dict):
            raise ValueError("COLLABORATION_POLICY_HAZARD_INVALID")
        domain_kinds = frozenset(value.get("domain_kinds", []))
        if not domain_kinds or not domain_kinds.issubset(ALLOWED_DOMAIN_KINDS[hazard]):
            raise ValueError("COLLABORATION_POLICY_DOMAIN_INVALID")
        hazards[hazard] = HazardCorrelationPolicy(
            hazard=hazard,
            domain_kinds=domain_kinds,
            window_seconds=int(value["window_seconds"]),
            min_independent_peers=int(value["min_independent_peers"]),
            allowed_observations=frozenset(value.get("allowed_observations", [])),
            email_unverified_action=value["email_unverified_action"],
            fixture_qualified_action=value["fixture_qualified_action"],
            require_clock_band_at_most=value.get("require_clock_band_at_most"),
        )
    if set(hazards) != set(ALLOWED_DOMAIN_KINDS):
        raise ValueError("COLLABORATION_POLICY_MUST_COVER_EXACTLY_FOUR_HAZARDS")
    return CollaborationPolicy(policy_version=str(raw["policy_version"]), hazards=hazards)


def validate_signal(
    signal: CollaborativeSignal,
    *,
    now: datetime | None = None,
    policy: CollaborationPolicy | None = None,
) -> tuple[str, ...]:
    now = now or datetime.now(timezone.utc)
    policy = policy or load_policy()
    reasons: list[str] = []
    hp = policy.hazards[signal.hazard]
    if signal.expires_at <= now:
        reasons.append("SIGNAL_EXPIRED")
    if signal.source_mode == "replayed":
        reasons.append("SOURCE_MODE_REPLAYED")
    if signal.correlation_domain.kind == "unknown":
        reasons.append("DOMAIN_UNKNOWN")
    elif signal.correlation_domain.kind not in hp.domain_kinds:
        reasons.append("HAZARD_DOMAIN_MISMATCH")
    if signal.observation not in hp.allowed_observations:
        # Supported schema observations such as a resolution update can be
        # retained as context without strengthening an active correlation.
        reasons.append("OBSERVATION_NOT_CORRELATION_ELIGIBLE")
    if hp.require_clock_band_at_most is not None:
        if CLOCK_RANK[signal.clock_uncertainty_band] > CLOCK_RANK[hp.require_clock_band_at_most]:
            reasons.append("CLOCK_UNSAFE")
    return tuple(reasons)


def _decision_id(policy_id: str, hazard: str, domain_id: str, now: datetime, signal_ids: list[str]) -> str:
    material = "|".join([policy_id, hazard, domain_id, now.isoformat(), *sorted(signal_ids)])
    return "corrdec_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def evaluate_correlation(
    signals: list[CollaborativeSignal],
    *,
    now: datetime | None = None,
    transport_trust: str = "fixture_qualified",
    policy: CollaborationPolicy | None = None,
) -> CorrelationDecisionRecord:
    """Evaluate one hazard/domain episode and emit an explainable decision record."""
    now = now or datetime.now(timezone.utc)
    policy = policy or load_policy()
    if not signals:
        raise ValueError("CORRELATION_REQUIRES_SIGNAL")

    anchor = signals[0]
    hp = policy.hazards[anchor.hazard]
    window = timedelta(seconds=hp.window_seconds)
    window_start = anchor.event_time_bucket - window
    window_end = anchor.event_time_bucket + window
    candidates: list[CollaborativeSignal] = []
    accepted: list[CollaborativeSignal] = []
    rejected: list[CollaborativeSignal] = []
    peer_candidates: list[CollaborativeSignal] = []
    blocking: list[str] = []

    for signal in signals:
        candidates.append(signal)
        mismatch = signal.hazard != anchor.hazard or signal.correlation_domain.kind != anchor.correlation_domain.kind or signal.correlation_domain.id != anchor.correlation_domain.id
        in_window = window_start <= signal.event_time_bucket <= window_end
        reasons = validate_signal(signal, now=now, policy=policy)
        if mismatch:
            reasons = (*reasons, "CORRELATION_KEY_MISMATCH")
        if not in_window:
            reasons = (*reasons, "OUTSIDE_POLICY_WINDOW")
        # Clock quality is a correlation-strength guard rather than a claim
        # that the peer did not exist.  It therefore blocks an earthquake
        # trigger while the diagnostic peer count can still show how many
        # independent contributors were observed.
        non_clock_reasons = tuple(reason for reason in reasons if reason != "CLOCK_UNSAFE")
        if not non_clock_reasons:
            peer_candidates.append(signal)
        if reasons:
            rejected.append(signal)
            blocking.extend(reasons)
        else:
            accepted.append(signal)

    # At most one contribution from a peer counts toward independence.  The
    # count is diagnostic; action selection below additionally requires safe
    # clock quality for hazards that declare it.
    peers = {signal.node_pseudonym for signal in peer_candidates}
    positive: list[str] = []
    if len(peers) >= hp.min_independent_peers:
        positive.extend(["MIN_PEERS_MET", "DOMAIN_MATCH", "POLICY_WINDOW_MATCH"])
    else:
        blocking.append("MIN_PEERS_NOT_MET")

    selected_action: Action = "no_action"
    if anchor.correlation_domain.kind == "unknown":
        selected_action = "context_only"
        blocking.append("DOMAIN_UNKNOWN")
    elif len(peers) >= hp.min_independent_peers and "CLOCK_UNSAFE" not in blocking:
        if transport_trust == "email_unverified":
            selected_action = hp.email_unverified_action
            positive.append("EMAIL_UNVERIFIED_REVIEW_ONLY")
        elif transport_trust == "fixture_qualified":
            selected_action = hp.fixture_qualified_action
            positive.append("FIXTURE_QUALIFIED_SIMULATION")
        elif transport_trust == "authenticated_peer":
            # v0.1 has no qualified authenticated-peer production path.  Never
            # upgrade it to a trusted confirmation merely because a label says
            # authenticated.
            selected_action = "create_review_incident"
            blocking.append("AUTHENTICATED_PEER_PATH_NOT_QUALIFIED_V1")
        else:
            selected_action = "no_action"
            blocking.append("PEER_UNTRUSTED")

    incident_id = None
    if selected_action in {"create_review_incident", "update_incident", "multi_node_trigger_simulated"}:
        digest = hashlib.sha256(f"{anchor.hazard}|{anchor.correlation_domain.kind}|{anchor.correlation_domain.id}".encode()).hexdigest()[:20]
        incident_id = f"collab-{anchor.hazard}-{digest}"

    candidate_ids = [item.signal_id for item in candidates]
    return CorrelationDecisionRecord(
        decision_id=_decision_id(policy.policy_version, anchor.hazard, anchor.correlation_domain.id, now, candidate_ids),
        policy_id=policy.policy_version,
        hazard=anchor.hazard,
        domain_kind=anchor.correlation_domain.kind,
        domain_id=anchor.correlation_domain.id,
        window_start=window_start,
        window_end=window_end,
        candidate_signal_ids=candidate_ids,
        accepted_signal_ids=[item.signal_id for item in accepted],
        rejected_signal_ids=[item.signal_id for item in rejected],
        independent_peer_count=len(peers),
        selected_action=selected_action,
        positive_reasons=list(dict.fromkeys(positive)),
        blocking_reasons=list(dict.fromkeys(blocking)),
        created_or_updated_incident_id=incident_id,
        created_at=now,
    )


def correlate(
    signals: list[CollaborativeSignal],
    *,
    now: datetime | None = None,
    window: timedelta | None = None,
    transport_trust: str = "fixture_qualified",
) -> CorrelationDecision:
    """Compatibility facade using the formal hazard policy.

    ``window`` is retained for source compatibility; the released policy is
    authoritative and therefore an arbitrary caller-supplied window cannot
    broaden the correlation envelope.
    """
    if not signals:
        return CorrelationDecision("NO_CORRELATION", ("INSUFFICIENT_INDEPENDENT_PEERS",), 0, transport_trust)
    record = evaluate_correlation(signals, now=now, transport_trust=transport_trust)
    action_map = {
        "no_action": "NO_CORRELATION",
        "context_only": "CONTEXT_ONLY",
        "create_review_incident": "REVIEW_REQUIRED",
        "update_incident": "REVIEW_REQUIRED",
        "multi_node_trigger_simulated": "MULTI_NODE_TRIGGER_SIMULATED",
    }
    reasons = tuple(record.positive_reasons or record.blocking_reasons)
    if record.selected_action == "no_action" and "MIN_PEERS_NOT_MET" in record.blocking_reasons:
        reasons = ("INSUFFICIENT_INDEPENDENT_PEERS",)
    if record.selected_action == "create_review_incident" and transport_trust == "email_unverified":
        reasons = ("EMAIL_UNVERIFIED_TRANSPORT",)
    if record.selected_action == "multi_node_trigger_simulated":
        reasons = ("INDEPENDENT_PEERS_MATCHED",)
    return CorrelationDecision(action_map[record.selected_action], reasons, record.independent_peer_count, transport_trust)
