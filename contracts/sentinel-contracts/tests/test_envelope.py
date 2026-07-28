from uuid import uuid4
import pytest
from sentinel_contracts import Envelope, Problem

def test_round_trip_and_immutable_data():
    e = Envelope("observation.created", "module-01", {"value": 1}, producer="collector")
    assert Envelope.from_dict(e.to_dict()).to_dict() == e.to_dict()
    with pytest.raises(TypeError): e.data["x"] = 2

def test_hostile_and_unknown_values_are_rejected():
    with pytest.raises(ValueError): Envelope("bad name", "source", {})
    with pytest.raises(ValueError): Envelope.from_dict({"type":"x", "source":"source", "id":str(uuid4()), "time":"2026-01-01T00:00:00+00:00", "data":{}, "extra":1})
    assert "password" not in str(Problem("bad", "Bad", "password=secret").to_dict())

def test_nested_values_and_metadata_are_immutable_and_validated():
    e = Envelope("observation.created", "module-01", {"nested": {"x": 1}, "items": [1]})
    with pytest.raises(TypeError): e.data["nested"]["x"] = 2
    with pytest.raises(AttributeError): e.data["items"].append(2)
    raw = e.to_dict(); raw["specversion"] = "999"
    with pytest.raises(ValueError): Envelope.from_dict(raw)
