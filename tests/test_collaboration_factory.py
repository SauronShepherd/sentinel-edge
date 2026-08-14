from datetime import datetime, timezone

from sentinel_edge.collaboration import (
    CollaborationConsent,
    CollaborationPrivacyTransformer,
    CollaborativeSignalFactory,
)


def _consent(*, sharing: bool = True, research: bool = False) -> CollaborationConsent:
    return CollaborationConsent(
        sharing_enabled=sharing,
        research_enabled=research,
        hazards={"wildfire": True, "earthquake": True, "flood": True, "landslide": True},
        policy_version="collab-consent-v1",
        updated_at=datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc),
    )


def test_factory_is_default_off_and_only_emits_material_states() -> None:
    privacy = CollaborationPrivacyTransformer(derivation_secret="local-secret")
    off = CollaborativeSignalFactory(
        enabled=False, consent=_consent(), privacy=privacy,
        node_identity_ref="private-node-serial", derivation_secret="factory-secret",
    )
    kwargs = dict(
        hazard="earthquake", local_event_ref="local-event-1", local_state="local_trigger",
        local_event_time=datetime(2026, 8, 13, 12, 0, 3, tzinfo=timezone.utc),
        local_location_ref="37.7749,-122.4194", confidence_band="high", coverage_band="good",
        sensor_health="healthy", clock_uncertainty_band="low", source_mode="simulated",
    )
    assert off.build_from_local_event(**kwargs) is None

    on = CollaborativeSignalFactory(
        enabled=True, consent=_consent(), privacy=privacy,
        node_identity_ref="private-node-serial", derivation_secret="factory-secret",
    )
    assert on.build_from_local_event(**{**kwargs, "local_state": "continuous_acceleration_sample"}) is None
    signal = on.build_from_local_event(**kwargs)
    assert signal is not None
    assert signal.sequence == 0
    assert signal.correlation_domain.kind == "spatial_cell"
    assert "37.7749" not in signal.model_dump_json()
    assert "private-node-serial" not in signal.model_dump_json()
    assert signal.research_use_allowed is False


def test_factory_keeps_episode_stable_and_increments_sequence() -> None:
    privacy = CollaborationPrivacyTransformer(derivation_secret="local-secret")
    factory = CollaborativeSignalFactory(
        enabled=True, consent=_consent(research=True), privacy=privacy,
        node_identity_ref="node-ref", derivation_secret="factory-secret",
    )
    base = dict(
        hazard="wildfire", local_event_ref="event-A", local_event_time=datetime(2026, 8, 13, 12, 0, 12, tzinfo=timezone.utc),
        local_location_ref="camera-private-location", local_sensor_context_ref="camera_sector:sector-private-07",
        confidence_band="medium", coverage_band="partial", sensor_health="healthy",
        clock_uncertainty_band="low", source_mode="simulated",
    )
    first = factory.build_from_local_event(local_state="possible_smoke", **base)
    second = factory.build_from_local_event(local_state="persistent_smoke", **base)
    assert first is not None and second is not None
    assert first.episode_id == second.episode_id
    assert (first.sequence, second.sequence) == (0, 1)
    assert first.signal_id != second.signal_id
    assert first.research_use_allowed is True
    assert first.correlation_domain.kind == "camera_sector"
    assert first.event_time_bucket.second == 0


def test_research_consent_never_enables_sharing_by_itself() -> None:
    privacy = CollaborationPrivacyTransformer(derivation_secret="local-secret")
    # The contract model itself rejects the invalid OFF/ON state.
    try:
        _consent(sharing=False, research=True)
    except ValueError as exc:
        assert "RESEARCH_REQUIRES_SHARING" in str(exc)
    else:
        raise AssertionError("research-only consent was accepted")
