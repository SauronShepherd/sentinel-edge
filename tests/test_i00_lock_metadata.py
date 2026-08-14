from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_offline_lock_metadata_check_does_not_require_registry_access() -> None:
    result = subprocess.run([sys.executable, "scripts/check_lock_metadata.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
