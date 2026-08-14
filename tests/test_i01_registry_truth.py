from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_registry_validator_rejects_verified_without_receipt(tmp_path: Path) -> None:
    registry = ROOT / "registries" / "tasks.yaml"
    copied = tmp_path / "repo"
    copied.mkdir()
    (copied / "registries").mkdir()
    for name in ("tasks.yaml", "tests.yaml", "iterations.yaml"):
        (copied / "registries" / name).write_text((ROOT / "registries" / name).read_text(encoding="utf-8"), encoding="utf-8")
    text = (copied / "registries" / "tasks.yaml").read_text(encoding="utf-8").replace("status: PLANNED", "status: VERIFIED", 1)
    (copied / "registries" / "tasks.yaml").write_text(text, encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/validate_delivery_registry.py", "--root", str(copied)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1
    assert "verified_without_execution" in result.stdout
