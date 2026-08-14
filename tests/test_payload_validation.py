from datetime import datetime, timezone
from uuid import uuid4
import pytest
from sentinel_edge.exports import CapDraftValidationError, build_cap_test_draft, validate_cap_test_document
from sentinel_edge.geospatial import validate_geojson_geometry
from sentinel_edge.integrations import XmlPayloadValidationError, validate_xml_payload

def test_invalid_cap_geojson_and_xml_payloads_are_rejected() -> None:
    draft = build_cap_test_draft(incident_id=uuid4(), sender="sentinel-edge.local", event="test", description="review", sent=datetime(2026, 8, 12, tzinfo=timezone.utc))
    with pytest.raises(CapDraftValidationError):
        validate_cap_test_document(draft.xml.replace(b">Test<", b">Actual<"))
    assert validate_geojson_geometry({"type": "Point", "coordinates": [999, 999]}).decision.value == "rejected"
    with pytest.raises(XmlPayloadValidationError):
        validate_xml_payload(b"<!DOCTYPE alert [<!ENTITY x SYSTEM 'file:///secret'>]><alert>&x;</alert>")
    with pytest.raises(XmlPayloadValidationError):
        validate_xml_payload(b"<alert>")

def test_xml_validation_reports_bounded_valid_payload() -> None:
    raw = b"<alert><info><event>test</event></info></alert>"
    report = validate_xml_payload(raw)
    assert report == {"valid": True, "root": "alert", "bytes": len(raw), "depth": 3}
