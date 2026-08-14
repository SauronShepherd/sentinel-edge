from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_export_rejects_dirty_worktree() -> None:
    output = ROOT / ".tmp" / "r01-export-test"
    result = subprocess.run(
        [sys.executable, "scripts/export_source.py", "--output", str(output), "--require-clean"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert ("worktree_not_clean" in result.stdout) or ("git_metadata_unavailable" in result.stdout)
