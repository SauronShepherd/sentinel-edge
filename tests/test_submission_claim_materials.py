from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_submission_benchmark_materials_are_claim_registry_bound() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_submission_claim_materials.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Claim Registry and public B0/B1/O1 materials agree" in result.stdout
