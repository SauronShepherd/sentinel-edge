from __future__ import annotations

import ast
import json
from pathlib import Path

from sentinel_edge.privacy import build_privacy_closure, scan_repository_for_private_material, verify_privacy_closure, write_privacy_closure
from sentinel_edge.scenario import DeterministicScenarioEngine


def test_every_source_artifact_write_declares_a_policy() -> None:
    missing: list[str] = []
    for path in Path("src/sentinel_edge").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "put_bytes":
                if not any(item.arg == "policy" for item in node.keywords):
                    missing.append(f"{path}:{node.lineno}")
    assert missing == []


def test_privacy_closure_is_digest_bound_and_fails_on_private_material(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "README.md").write_text("safe public material\n", encoding="utf-8")
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    payload = build_privacy_closure(engine, repository_root=repository)
    assert payload["privacy_state_complete"] is True
    path = write_privacy_closure(engine, repository_root=repository, output=tmp_path / "privacy.json")
    assert verify_privacy_closure(path)["valid"] is True
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["artifact_catalog"]["registration_count"] = 999
    path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert verify_privacy_closure(path)["valid"] is False

    private_marker = "-----BEGIN " + "PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----\n"
    (repository / "leaked.pem").write_text(private_marker, encoding="utf-8")
    findings = scan_repository_for_private_material(repository)
    assert findings == ({"path": "leaked.pem", "category": "private_signing_key"},)
    failed = build_privacy_closure(engine, repository_root=repository)
    assert failed["privacy_state_complete"] is False
    assert "repository_private_material_detected" in failed["failures"]
