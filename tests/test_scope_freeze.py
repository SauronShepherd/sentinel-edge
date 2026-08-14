from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_scope_freeze import generate
from scripts.validate_scope_freeze import validate


ROOT = Path(__file__).resolve().parents[1]


def test_scope_freeze_is_current_and_complete() -> None:
    result = validate(ROOT)
    assert result == {"valid": True, "h0_count": 240, "failures": []}


def test_scope_freeze_detects_registry_drift(tmp_path: Path) -> None:
    (tmp_path / "qualification").mkdir()
    (tmp_path / "registries").mkdir()
    source = ROOT / "registries/requirements.yaml"
    (tmp_path / "registries/requirements.yaml").write_bytes(source.read_bytes())
    (tmp_path / "qualification/scope-freeze.json").write_text(json.dumps(generate(tmp_path)) + "\n", encoding="utf-8")
    mutated = (tmp_path / "registries/requirements.yaml").read_text(encoding="utf-8") + "\n"
    (tmp_path / "registries/requirements.yaml").write_text(mutated, encoding="utf-8")
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "scope_freeze_drift:requirements_sha256" in result["failures"]


def test_scope_freeze_rejects_exception_without_approver_or_reruns(tmp_path: Path) -> None:
    (tmp_path / "qualification").mkdir()
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries/requirements.yaml").write_bytes((ROOT / "registries/requirements.yaml").read_bytes())
    payload = generate(tmp_path)
    payload["exceptions"] = [{"exception_id": "x", "reason": "reason", "approver": "", "displaced_or_cut": "cut", "affected_requirements": ["REQ-X"], "mandatory_reruns": []}]
    (tmp_path / "qualification/scope-freeze.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "exception[0]:blank:approver" in result["failures"]
    assert "exception[0]:empty:mandatory_reruns" in result["failures"]
