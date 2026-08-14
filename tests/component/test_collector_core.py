from datetime import datetime, timezone, timedelta
from importlib import import_module
Observation = import_module("sentinel_streaming_source_collector.domain").Observation
TimeQuality = import_module("sentinel_streaming_source_collector.domain").TimeQuality
identity = import_module("sentinel_streaming_source_collector.domain").identity
AcquisitionPolicy = import_module("sentinel_streaming_source_collector.application.acquisition_policy").AcquisitionPolicy
PrivacyMinimizer = import_module("sentinel_streaming_source_collector.application.privacy_minimization").PrivacyMinimizer
SQLiteRepository = import_module("sentinel_streaming_source_collector.adapters.sqlite_repository").SQLiteRepository
CollectorPipeline = import_module("sentinel_streaming_source_collector.application.pipeline").CollectorPipeline

def test_observation_rejects_naive_time():
    try: Observation("s", "temperature", 1, "celsius", datetime.now(), "good")
    except ValueError: pass
    else: raise AssertionError("naive timestamps must fail")

def test_policy_and_privacy_gate():
    with_expiry = AcquisitionPolicy(True, datetime.now(timezone.utc) - timedelta(seconds=1))
    try: with_expiry.authorize()
    except PermissionError: pass
    else: raise AssertionError("expired policy must fail")
    assert PrivacyMinimizer().apply({"latitude": 1.234567, "person_id": "secret", "site": "a"}) == {"latitude": 1.235, "site": "a"}


def test_privacy_minimization_removes_all_restricted_fields_before_output():
    source = {
        "latitude": 1.23456789,
        "longitude": -2.9876543,
        "person_id": "person-1",
        "face": "raw-face-bytes",
        "raw_audio": b"private-audio",
        "address": "private-address",
        "site": "public-site",
    }
    minimized = PrivacyMinimizer(coordinate_precision=2).apply(source)
    assert minimized == {"latitude": 1.23, "longitude": -2.99, "site": "public-site"}
    assert source["person_id"] == "person-1"
    assert not set(minimized) & PrivacyMinimizer().restricted_fields

def test_pipeline_redelivery_is_idempotent():
    repo = SQLiteRepository(); output = []; pipeline = CollectorPipeline(repo)
    assert pipeline.ingest("fixture", [(1, b"payload"), (1, b"payload")], output.append) == 1
    assert output == [b"payload"] and repo.contains(identity("fixture", 1, b"payload"))

def test_time_quality_marks_age():
    captured = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert TimeQuality(captured, captured + timedelta(seconds=3), "boot").age_seconds == 3
