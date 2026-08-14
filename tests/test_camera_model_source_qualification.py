import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinel_edge.domain.models import CapabilityState, SourceMode
from sentinel_edge.qualification import (
    commission_camera,
    load_model_quality_manifest,
    load_source_observation,
    load_source_policy,
    qualify_model_quality,
    qualify_source,
    summarize_sources,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)


def test_camera_fixture_passes_quality_without_claiming_physical_device() -> None:
    report = commission_camera(
        "fixtures/camera/wildfire-camera-5fps-development.jsonl",
        source_id="wildfire-camera-development",
        requested_fps=5.0,
    )
    assert report.state is CapabilityState.TESTED
    assert report.physical_source_proven is False
    assert report.frame_count == 90
    assert report.sequence_gaps == 0
    assert report.frozen_frames == 0
    assert report.resolution_consistent is True
    assert "physical_camera_not_proven" in report.reason_codes


def test_camera_commissioning_rejects_freeze_darkness_and_sequence_defects(tmp_path: Path) -> None:
    source = tmp_path / "bad-camera.jsonl"
    base = NOW
    rows = []
    for index in range(10):
        rows.append({
            "sequence": index + (1 if index > 4 else 0),
            "monotonic_ns": index * 200_000_000,
            "captured_at": (base + timedelta(milliseconds=200 * index)).isoformat(),
            "received_at": (base + timedelta(milliseconds=200 * index)).isoformat(),
            "width": 640,
            "height": 480,
            "luminance_mean": 2.0,
            "blur_score": 1.0,
            "occlusion_fraction": 0.95,
            "frame_sha256": "a" * 64,
        })
    source.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    report = commission_camera(source, source_id="bad", requested_fps=5, minimum_frames=10)
    assert report.state is CapabilityState.FAILED
    assert "sequence_gaps" in report.reason_codes
    assert "frozen_frames_exceed_limit" in report.reason_codes
    assert "dark_frames_exceed_limit" in report.reason_codes
    assert "blurred_frames_exceed_limit" in report.reason_codes
    assert "occluded_frames_exceed_limit" in report.reason_codes


def test_model_quality_fixture_passes_guardrails_but_is_not_target_evidence() -> None:
    report = qualify_model_quality(
        load_model_quality_manifest("fixtures/models/wildfire-smoke-quality.manifest.json"),
        root=".",
        now=NOW,
    )
    assert report.state is CapabilityState.TESTED
    assert report.quality_guardrails_passed is True
    assert report.graph_quarantine_passed is True
    assert report.known_answer_passed is True
    assert report.split_leakage_detected is False
    assert report.recall == 1.0
    assert report.false_alarm_rate == 0.0
    assert report.target_qualified is False


def test_model_quality_rejects_group_leakage(tmp_path: Path) -> None:
    root = tmp_path
    manifest = load_model_quality_manifest("fixtures/models/wildfire-smoke-quality.manifest.json")
    model = root / manifest.model_path
    model.parent.mkdir(parents=True)
    model.write_bytes(Path(manifest.model_path).read_bytes())
    known = root / manifest.known_answer_path
    known.parent.mkdir(parents=True)
    known.write_bytes(Path(manifest.known_answer_path).read_bytes())
    rows = [json.loads(line) for line in Path(manifest.dataset_path).read_text().splitlines()]
    rows[-1][manifest.split_group_field] = rows[0][manifest.split_group_field]
    dataset = root / manifest.dataset_path
    dataset.parent.mkdir(parents=True, exist_ok=True)
    dataset.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    import hashlib
    changed = manifest.model_copy(update={"dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest()})
    report = qualify_model_quality(changed, root=root, now=NOW)
    assert report.state is CapabilityState.FAILED
    assert report.split_leakage_detected is True
    assert "split_group_leakage" in report.reason_codes


def test_source_policy_separates_fixture_readiness_from_live_release() -> None:
    report = qualify_source(
        load_source_policy("fixtures/sources/meteoalarm-fixture.policy.json"),
        load_source_observation("fixtures/sources/meteoalarm-fixture.observation.json"),
        now=NOW,
    )
    assert report.state is CapabilityState.TESTED
    assert report.decision_influence_allowed is True
    assert report.release_ready is False
    assert report.decision_state.value == "active"
    summary = summarize_sources([report])
    assert summary["h0_zero_live_source_valid"] is True
    assert summary["live_release_ready_count"] == 0


def test_source_policy_rejects_stale_and_terms_mismatch() -> None:
    policy = load_source_policy("fixtures/sources/meteoalarm-fixture.policy.json")
    observation = load_source_observation("fixtures/sources/meteoalarm-fixture.observation.json").model_copy(
        update={"source_event_at": NOW - timedelta(hours=1), "terms_revision": "wrong"}
    )
    report = qualify_source(policy, observation, now=NOW)
    assert report.decision_influence_allowed is False
    assert "source_stale" in report.reason_codes
    assert "terms_or_review_expired" in report.reason_codes
    assert report.decision_state.value == "review_required"


def test_model_quality_rejects_unresolved_license() -> None:
    manifest = load_model_quality_manifest("fixtures/models/wildfire-smoke-quality.manifest.json").model_copy(
        update={"license_id": "NOASSERTION"}
    )
    report = qualify_model_quality(manifest, root=".", now=NOW)
    assert report.state is CapabilityState.FAILED
    assert "model_license_unresolved" in report.reason_codes


def test_authenticated_source_cache_requires_scope_and_generation() -> None:
    policy = load_source_policy("fixtures/sources/meteoalarm-fixture.policy.json").model_copy(
        update={"authenticated_cache": True, "snapshot_generation_required": True, "source_mode": SourceMode.LIVE}
    )
    observation = load_source_observation("fixtures/sources/meteoalarm-fixture.observation.json").model_copy(
        update={"authenticated": True, "authorization_scope_sha256": None, "cache_context_sha256": None, "generation_id": None}
    )
    report = qualify_source(policy, observation, now=NOW)
    assert report.decision_influence_allowed is False
    assert "authenticated_cache_context_missing" in report.reason_codes
    assert "generation_evidence_missing" in report.reason_codes
