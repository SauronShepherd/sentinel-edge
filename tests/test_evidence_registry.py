from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from scripts.validate_evidence_registry import validate


def _write_registry(root: Path, items: list[dict[str, object]]) -> None:
    (root / "registries").mkdir(parents=True)
    (root / "registries/evidence.yaml").write_text(yaml.safe_dump({"items": items}), encoding="utf-8")


def test_current_evidence_registry_is_structurally_valid() -> None:
    result = validate(Path(__file__).parents[1])
    assert result["valid"] is True
    assert result["count"] == 350


def test_historical_unavailable_evidence_is_reported_not_promoted(tmp_path: Path) -> None:
    root = tmp_path
    _write_registry(root, [{
        "id": "EV-HISTORICAL",
        "kind": "TEST_RESULT",
        "summary": "externalized historical result",
        "path": "evidence/historical.txt",
        "sha256": "0" * 64,
        "captured_at": "2026-08-12T00:00:00Z",
        "producer": "pytest",
        "status": "ACTIVE",
    }])
    result = validate(root)
    assert result["valid"] is True
    assert result["unavailable"] == ["EV-HISTORICAL"]


def test_locally_available_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    artifact = tmp_path / "evidence/result.txt"
    artifact.parent.mkdir()
    artifact.write_text("actual\n", encoding="utf-8")
    _write_registry(tmp_path, [{
        "id": "EV-MISMATCH",
        "kind": "TEST_RESULT",
        "summary": "mismatched result",
        "path": "evidence/result.txt",
        "sha256": hashlib.sha256(b"expected\n").hexdigest(),
        "captured_at": "2026-08-12T00:00:00Z",
        "producer": "pytest",
        "status": "ACTIVE",
    }])
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "digest_mismatch:EV-MISMATCH" in result["failures"]


def test_resolved_symlink_path_outside_root_fails_closed(tmp_path: Path) -> None:
    outside = tmp_path.parent / "evidence-registry-outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    link = tmp_path / "evidence/link.txt"
    link.parent.mkdir()
    try:
        link.symlink_to(outside)
    except OSError:
        # Symlink creation is policy-controlled on some Windows runners.
        return
    _write_registry(tmp_path, [{
        "id": "EV-SYMLINK",
        "kind": "TEST_RESULT",
        "summary": "symlink escape",
        "path": "evidence/link.txt",
        "sha256": hashlib.sha256(b"secret\n").hexdigest(),
        "captured_at": "2026-08-12T00:00:00Z",
        "producer": "pytest",
        "status": "ACTIVE",
    }])
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "resolved_path_outside_root:EV-SYMLINK" in result["failures"]
