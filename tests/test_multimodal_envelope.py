from datetime import datetime, timezone

import pytest

from sentinel_edge.evidence.multimodal import EvidenceModality, MultimodalEvidenceEnvelope


def test_multimodal_envelope_preserves_fixture_contract() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    envelope = MultimodalEvidenceEnvelope(evidence_id="fixture-1", modality=EvidenceModality.VIDEO,
        origin="fixture:camera-1", captured_at=now, received_at=now, rights_basis="fixture-license",
        content_sha256="a" * 64, metadata={"source": "camera"})
    assert envelope.modality is EvidenceModality.VIDEO
    assert envelope.origin == "fixture:camera-1"
    assert envelope.content_sha256 == "a" * 64


def test_multimodal_envelope_rejects_bad_rights_and_time() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        MultimodalEvidenceEnvelope(evidence_id="fixture-1", modality=EvidenceModality.TEXT,
            origin="fixture", captured_at=now, received_at=now, rights_basis=" ", content_sha256="a" * 64)
