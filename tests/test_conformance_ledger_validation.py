from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.validate_conformance_ledger import validate


ROOT = Path(__file__).resolve().parents[1]


def test_generated_projections_have_no_drift() -> None:
    assert validate(ROOT) == {"valid": True, "failures": []}


def test_hand_edited_completion_status_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "qualification").mkdir()
    for name in ("conformance-ledger.json", "release-acceptance-checklist.json"):
        shutil.copy2(ROOT / "qualification" / name, tmp_path / "qualification" / name)
    # The generator also needs the authoritative inputs.
    for source in (ROOT / "registries").glob("*.yaml"):
        (tmp_path / "registries").mkdir(exist_ok=True)
        shutil.copy2(source, tmp_path / "registries" / source.name)
    for source in (ROOT / "docs/contracts").glob("*.md"):
        (tmp_path / "docs/contracts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, tmp_path / "docs/contracts" / source.name)
    path = tmp_path / "qualification/release-acceptance-checklist.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["status"] = "VERIFIED"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    result = validate(tmp_path)
    assert result["valid"] is False
    assert "projection_drift:qualification/release-acceptance-checklist.json" in result["failures"]
