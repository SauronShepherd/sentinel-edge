from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_format_gate_accepts_current_receipts_and_source() -> None:
    result = subprocess.run([sys.executable, "scripts/check_format.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "format check: PASS" in result.stdout
