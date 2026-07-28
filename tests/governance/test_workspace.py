
from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_and_lock_are_consistent() -> None:
    # The managed Windows image exposes uv as a WinGet shim that cannot be
    # spawned by child processes.  The locked development environment already
    # contains the same pinned uv release, so invoke it through this interpreter.
    env = os.environ.copy()
    env["UV_CACHE_DIR"] = str(ROOT / "build" / "uv-cache")
    result = subprocess.run([sys.executable, "-m", "uv", "lock", "--check", "--offline"], cwd=ROOT, env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_makefile_exposes_canonical_targets() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("setup:", "format-check:", "lint:", "type:", "architecture:", "governance:", "gates:"):
        assert target in text


def test_readme_identifies_all_six_modules() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for number in range(1, 7):
        assert f"{number}." in text
    assert "not an official emergency-warning service" in text
