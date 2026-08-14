from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.generate_claim_registry import generate
from scripts.generate_claim_registry import render_claim_table
from scripts.validate_claim_registry import validate
from sentinel_edge.domain.models import ClaimClass, ClaimRecord
from sentinel_edge.release import ClaimRegistry


ROOT = Path(__file__).resolve().parents[1]


def test_generated_claim_registry_preserves_development_ceiling() -> None:
    payload, table = generate(ROOT)
    assert payload["claim_ceiling"]["target_measurement_claim_allowed"] is False
    assert payload["claims"][0]["claim_class"] == "simulated"
    assert "Numeric performance values are not emitted" in table
    assert validate(ROOT)["valid"] is True


def test_generated_claim_registry_is_deterministic() -> None:
    first, first_table = generate(ROOT)
    second, second_table = generate(ROOT)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first_table == second_table


def test_release_table_is_rendered_from_registry_records() -> None:
    registry = ClaimRegistry()
    registry.add(ClaimRecord(claim_id="claim-b", claim_class=ClaimClass.SIMULATED, statement="second", artifact_refs=()))
    registry.add(ClaimRecord(claim_id="claim-a", claim_class=ClaimClass.SIMULATED, statement="first", artifact_refs=()))
    table = render_claim_table(registry, target_allowed=False)
    assert table.index("claim-a") < table.index("claim-b")
    assert "second" in table


def test_classification_report_labels_every_value_class() -> None:
    registry = ClaimRegistry()
    for claim_class in ClaimClass:
        measured = claim_class is ClaimClass.MEASURED
        registry.add(ClaimRecord(
            claim_id=f"claim-{claim_class.value}",
            claim_class=claim_class,
            statement=f"{claim_class.value} value",
            artifact_refs=("sha256:" + "a" * 64,) if measured else (),
            capability_hashes=("b" * 64,) if measured else (),
            config_hashes=("c" * 64,) if measured else (),
        ))
    report = registry.classification_report()
    assert report["schema"] == "sentinel-edge-claim-classification-report/1.0"
    assert report["unlabelled_count"] == 0
    assert {row["value_class"] for row in report["values"]} == {item.value for item in ClaimClass}
    assert all(row["label"] == row["value_class"] for row in report["values"])


def test_hand_entered_performance_value_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "qualification").mkdir()
    for name in ("claim-registry.json", "benchmark-evidence-report.json", "benchmark-identity-report.json"):
        source = ROOT / ("qualification/" + name)
        shutil.copy2(source, tmp_path / "qualification" / name)
    path = tmp_path / "qualification/claim-registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["claims"][0]["statement"] = "42% faster than baseline"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "hand_entered_performance_value:benchmark-local-development" in result["failures"]


def test_unregistered_claim_artifact_reference_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "qualification").mkdir()
    for name in ("claim-registry.json", "benchmark-evidence-report.json", "benchmark-identity-report.json"):
        source = ROOT / ("qualification/" + name)
        shutil.copy2(source, tmp_path / "qualification" / name)
    path = tmp_path / "qualification/claim-registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["claims"][0]["artifact_refs"] = ["sha256:" + "f" * 64]
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "claim_artifact_ref_unregistered:benchmark-local-development" in result["failures"]
