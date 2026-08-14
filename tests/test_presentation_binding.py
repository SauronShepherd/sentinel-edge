import json
from pathlib import Path

from sentinel_edge.release.presentation_binding import build_presentation_binding, verify_presentation_binding


def test_presentation_binding_rejects_artifact_or_candidate_drift(tmp_path: Path) -> None:
    registry = tmp_path / "qualification" / "claim-registry.json"
    registry.parent.mkdir()
    registry.write_text(json.dumps({"schema": "sentinel-edge-claim-registry/1.0", "claims": [], "source_artifacts": []}) + "\n", encoding="utf-8")
    demo = tmp_path / "demo.mp4"
    demo.write_bytes(b"demo-v1")
    candidate = {"candidate_id": "candidate-1"}
    binding = build_presentation_binding(candidate, registry, [demo], root=tmp_path)
    assert verify_presentation_binding(binding, candidate, root=tmp_path)["valid"]
    demo.write_bytes(b"demo-v2")
    result = verify_presentation_binding(binding, candidate, root=tmp_path)
    assert not result["valid"]
    assert "artifact_mismatch:demo.mp4" in result["failures"]
    assert "candidate_binding_mismatch" in verify_presentation_binding(binding, {"candidate_id": "other"}, root=tmp_path)["failures"]
