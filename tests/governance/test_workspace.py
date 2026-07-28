
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_and_lock_are_consistent() -> None:
    result = subprocess.run(["uv", "lock", "--check", "--offline"], cwd=ROOT, text=True, capture_output=True)
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
