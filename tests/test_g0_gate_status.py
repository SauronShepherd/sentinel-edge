from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_g0_gate_status import main as validate_g0_gate_status


def test_generated_status_contains_all_contract_gate_packs() -> None:
    payload = json.loads(Path("qualification/g0-gate-status.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["packs"]] == [f"G0-{index:02d}" for index in range(1, 13)]
    assert payload["summary"] == {"fail": 0, "pass": 12, "total": 12}
    assert payload["release_admitted"] is True
    assert payload["evidence_class"] == "emulated_profile"
    assert all(not pack["target_evidence_backed"] for pack in payload["packs"])
    for pack in payload["packs"]:
        assert pack["requirements"]
        assert all(requirement_id.startswith("REQ-") for requirement_id in pack["requirements"])
        assert pack["tests"]
        assert pack["artifacts"]
        assert pack["mapping_source"].endswith("sentinel-edge-full-scope-technical-contract-v0.22.0.md")

    manifest = json.loads(Path("qualification/release-minimum-manifest.json").read_text(encoding="utf-8"))
    mapped = {requirement_id for pack in payload["packs"] for requirement_id in pack["requirements"]}
    assert mapped == {row["requirement_id"] for row in manifest["rows"]}


def test_validator_rejects_mutated_projection(tmp_path: Path, monkeypatch) -> None:
    source = Path("qualification/g0-gate-status.json")
    mutated = tmp_path / "g0-gate-status.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["packs"][0]["status"] = "not_applicable"
    mutated.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    import scripts.validate_g0_gate_status as validator

    monkeypatch.setattr(validator, "OUTPUT", mutated)
    assert validate_g0_gate_status() == 1


def test_validator_rejects_incomplete_pack_mapping(tmp_path: Path, monkeypatch) -> None:
    source = Path("qualification/g0-gate-status.json")
    mutated = tmp_path / "g0-gate-status.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["packs"][0]["requirements"] = payload["packs"][0]["requirements"][1:]
    mutated.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    import scripts.validate_g0_gate_status as validator

    monkeypatch.setattr(validator, "OUTPUT", mutated)
    assert validate_g0_gate_status() == 1
