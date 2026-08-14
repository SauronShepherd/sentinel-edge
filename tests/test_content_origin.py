from uuid import uuid4

import pytest

from sentinel_edge.domain.models import ClaimNode, ContentOrigin, HazardKind


def test_claim_origin_and_lineage_round_trip_for_export_payload() -> None:
    claim = ClaimNode(
        incident_id=uuid4(),
        hazard=HazardKind.WILDFIRE,
        statement="Operator-reviewed source summary",
        origin=ContentOrigin.DETERMINISTIC_TRANSFORM,
        lineage=("source:meteoalarm", "transform:severity-v1"),
    )

    payload = claim.model_dump(mode="json")

    assert payload["origin"] == "deterministic_transform"
    assert payload["lineage"] == ["source:meteoalarm", "transform:severity-v1"]


def test_claim_origin_rejects_unclassified_values() -> None:
    with pytest.raises(ValueError):
        ClaimNode(
            incident_id=uuid4(),
            hazard=HazardKind.FLOOD,
            statement="untrusted label",
            origin="invented_origin",
        )


def test_generated_claim_requires_model_and_lineage_provenance() -> None:
    with pytest.raises(ValueError, match="model_id"):
        ClaimNode(incident_id=uuid4(), hazard=HazardKind.FLOOD, statement="caption", origin=ContentOrigin.GENERATIVE_MODEL)
    claim = ClaimNode(
        incident_id=uuid4(), hazard=HazardKind.FLOOD, statement="caption",
        origin=ContentOrigin.GENERATIVE_MODEL, model_id="caption-model:v1", lineage=("source:evidence-1",),
    )
    assert claim.model_id == "caption-model:v1"
