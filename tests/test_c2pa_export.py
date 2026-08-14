import pytest

from sentinel_edge.exports.c2pa import C2paExportCredential


def test_c2pa_credential_records_transformation_without_sensor_truth() -> None:
    credential = C2paExportCredential("sha256:asset", ("resize", "redact"), "sentinel-edge")
    metadata = credential.as_export_metadata()
    assert metadata["transformations"] == ["resize", "redact"]
    assert metadata["sensor_truth_claim"] is False


def test_c2pa_sensor_truth_claim_is_rejected() -> None:
    with pytest.raises(ValueError, match="sensor truth"):
        C2paExportCredential("sha256:asset", ("resize",), "issuer", sensor_truth_claim=True)
