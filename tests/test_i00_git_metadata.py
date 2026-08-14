from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_export_reports_missing_git_metadata_structurally(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("clean\n", encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/export_source.py", "--root", str(source), "--output", str(tmp_path / "out"), "--require-clean"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1
    assert "git_metadata_unavailable" in result.stdout
