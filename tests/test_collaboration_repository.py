from datetime import datetime, timedelta, timezone

from sentinel_edge.collaboration import (
    CollaborativeSignal,
    CollaborativeSignalEnvelope,
    CorrelationDecisionRecord,
    CorrelationDomain,
    SqliteCollaborationRepository,
)


def _envelope(signal_id: str, *, peer: str = "peer_1234567890123456") -> CollaborativeSignalEnvelope:
    now = datetime(2026, 8, 13, 12, tzinfo=timezone.utc)
    signal = CollaborativeSignal(
        signal_id=signal_id, episode_id="episode_1234567890123456", sequence=0,
        node_pseudonym=peer, hazard="earthquake", observation="local_trigger",
        correlation_domain=CorrelationDomain(kind="spatial_cell", id="cell:demo"),
        event_time_bucket=now, confidence_band="high", coverage_band="good",
        sensor_health="healthy", clock_uncertainty_band="low", source_mode="simulated",
        sharing_policy_version="collab-consent-v1", research_use_allowed=False,
        expires_at=now + timedelta(minutes=5),
    )
    return CollaborativeSignalEnvelope(
        received_at=now, transport="fixture", transport_message_id="msg-" + signal_id,
        transport_trust="fixture_qualified", signal=signal, validation_state="admitted",
        correlation_id="corr-12345678-" + signal_id,
    )


def test_sqlite_repository_is_module_owned_minimized_and_idempotent(tmp_path) -> None:
    repo = SqliteCollaborationRepository(str(tmp_path / "incidents" / "collaboration.db"), max_envelopes=4, max_decisions=4)
    env = _envelope("signal_1234567890123456")
    assert repo.add_envelope(env) is True
    assert repo.add_envelope(env) is False
    assert repo.envelopes() == (env,)
    raw = (tmp_path / "incidents" / "collaboration.db").read_bytes()
    assert b"raw camera" not in raw and b"OAuth" not in raw


def test_sqlite_repository_persists_decision_and_contributions(tmp_path) -> None:
    repo = SqliteCollaborationRepository(str(tmp_path / "incidents" / "collaboration.db"))
    env = _envelope("signal_abcdefghijklmnop")
    assert repo.add_envelope(env)
    now = datetime(2026, 8, 13, 12, tzinfo=timezone.utc)
    decision = CorrelationDecisionRecord(
        decision_id="decision_12345678", policy_id="collab-demo-v1", hazard="earthquake",
        domain_kind="spatial_cell", domain_id="cell:demo", window_start=now,
        window_end=now + timedelta(seconds=10), candidate_signal_ids=[env.signal.signal_id],
        accepted_signal_ids=[env.signal.signal_id], rejected_signal_ids=[], independent_peer_count=1,
        selected_action="no_action", positive_reasons=[], blocking_reasons=["MIN_PEERS_NOT_MET"],
        created_at=now,
    )
    repo.add_decision(decision)
    assert repo.decisions() == (decision,)
    assert repo.episode_envelopes(env) == [env]
