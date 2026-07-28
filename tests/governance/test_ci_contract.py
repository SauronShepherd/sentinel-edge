
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflows_satisfy_contract() -> None:
    result = subprocess.run([sys.executable, "scripts/validate_ci_workflows.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_full_gate_uploads_evidence_even_on_failure() -> None:
    text = (ROOT / ".github/workflows/ci-full.yml").read_text(encoding="utf-8")
    assert "if: always()" in text
    assert "actions/upload-artifact@v4" in text


def test_aggregate_depends_on_full_gate() -> None:
    text = (ROOT / ".github/workflows/ci-full.yml").read_text(encoding="utf-8")
    assert "needs: [full-gate]" in text
