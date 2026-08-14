from datetime import datetime, timezone

import pytest

from sentinel_edge.qualification.upload_envelope import normalize_uploaded_envelope


def payload() -> dict:
    now = datetime(2026, 8, 13, tzinfo=timezone.utc).isoformat()
    return {"source_id": "upload-source", "hazard": "wildfire", "source_mode": "simulated", "sequence": 1,
            "observed_at": now, "received_at": now, "values": {"smoke": 0.5}, "units": {"smoke": "ratio"}}


def test_upload_requires_normalized_envelope_before_analysis() -> None:
    envelope = normalize_uploaded_envelope(upload_sha256="a" * 64, payload=payload())
    assert envelope.analysis_allowed
    assert envelope.contract.schema_version == "2.0.0"


def test_upload_without_digest_or_valid_observation_is_rejected() -> None:
    with pytest.raises(ValueError, match="digest"):
        normalize_uploaded_envelope(upload_sha256="", payload=payload())
    with pytest.raises(Exception):
        normalize_uploaded_envelope(upload_sha256="b" * 64, payload={"source_id": "missing"})
