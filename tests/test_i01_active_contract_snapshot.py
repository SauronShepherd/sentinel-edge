from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_active_contract_snapshot_is_deterministic_and_truthful(tmp_path: Path) -> None:
    output = tmp_path / "snapshot.json"
    result = subprocess.run([sys.executable, "scripts/generate_active_contract_snapshot.py", "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "0.22.0"
    assert payload["profile"] == "H0"
    assert payload["registries"]["requirements.yaml"]["count"] == 743
    assert payload["release_claims"]["release_admitted"] is False
