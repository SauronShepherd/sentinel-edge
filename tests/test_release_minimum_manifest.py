from __future__ import annotations

from pathlib import Path

from scripts.generate_release_minimum_manifest import generate


ROOT = Path(__file__).resolve().parents[1]


def test_release_minimum_manifest_generates_critical_path_and_automatic_cut() -> None:
    manifest = generate(ROOT)
    assert manifest["critical_path"]["status"] == "complete"
    assert len(manifest["critical_path"]["open_requirement_ids"]) == 0
    assert manifest["automatic_cut"] == {
        "status": "clear",
        "release_admitted": True,
        "reason_codes": [],
        "open_count": 0,
    }
    assert len(set(manifest["critical_path"]["open_requirement_ids"])) == 0
    assert all(row["slice"] for row in manifest["rows"])
