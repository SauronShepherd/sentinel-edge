
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_source_baseline_hashes_and_index() -> None:
    result = subprocess.run([sys.executable, "scripts/validate_source_baseline.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "14 specifications" in result.stdout
