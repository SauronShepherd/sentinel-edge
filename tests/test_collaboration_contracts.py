from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from sentinel_edge.collaboration import CollaborativeSignal, CollaborationConsent

def payload(**overrides):
    value = {"signal_id": "signal-1234567890", "episode_id": "episode-1234567890", "sequence": 0, "node_pseudonym": "node-pseudonym-1234", "hazard": "earthquake", "observation": "local_trigger", "correlation_domain": {"kind": "spatial_cell", "id": "cell:coarse-1"}, "event_time_bucket": datetime.now(timezone.utc), "confidence_band": "medium", "coverage_band": "good", "sensor_health": "healthy", "clock_uncertainty_band": "low", "source_mode": "simulated", "sharing_policy_version": "1", "research_use_allowed": False, "expires_at": datetime.now(timezone.utc)}
    value.update(overrides)
    return value

def test_signal_rejects_unknown_observation():
    with pytest.raises(ValidationError, match="UNSUPPORTED_OBSERVATION"):
        CollaborativeSignal.model_validate(payload(observation="unknown_event"))

def test_signal_rejects_exact_coordinate_fields():
    with pytest.raises(ValidationError):
        CollaborativeSignal.model_validate(payload(latitude=40.0))

def test_consent_research_requires_sharing():
    with pytest.raises(ValidationError, match="RESEARCH_REQUIRES_SHARING"):
        CollaborationConsent(sharing_enabled=False, research_enabled=True, hazards={"earthquake": True, "wildfire": False, "flood": False, "landslide": False}, policy_version="1", updated_at=datetime.now(timezone.utc))
