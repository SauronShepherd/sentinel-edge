from __future__ import annotations

import json
from pathlib import Path

from sentinel_edge.release.reproducibility import write_release_lock
from sentinel_edge.security import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def test_release_lock_is_a_deterministic_projection_of_uv_lock(tmp_path: Path) -> None:
    first = write_release_lock(ROOT, tmp_path / "first.json")
    second = write_release_lock(ROOT, tmp_path / "second.json")
    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["resolution_kind"] == "uv_lock_projection"
    assert payload["complete"] is True
    assert payload["missing_direct_requirements"] == []
    assert payload["uv_lock_sha256"] == sha256_file(ROOT / "uv.lock")
    assert payload["python"] == ">=3.11, <3.14"
    locked = {item["name"].lower(): item["version"] for item in payload["resolved"]}
    assert locked["cryptography"] == "46.0.7"
    assert locked["packaging"] == "25.0"
