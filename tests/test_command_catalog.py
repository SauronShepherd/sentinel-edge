from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.validate_command_catalog import validate


ROOT = Path(__file__).resolve().parents[1]


def test_command_catalog_is_valid_and_nonempty() -> None:
    result = validate(ROOT)
    assert result == {"valid": True, "count": 50, "failures": []}


def test_command_catalog_rejects_undocumented_test_alias() -> None:
    names = [item["name"] for item in __import__("yaml").safe_load(
        (ROOT / "architecture/command-catalog.yaml").read_text(encoding="utf-8")
    )["commands"]]
    assert "test" not in names
    assert "test-all" in names
    assert "test-arm" in names


def test_dev_help_is_projected_from_the_catalog() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dev.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    for name in ("setup", "verify", "gates", "test-workstream", "e2e-iteration"):
        assert name in result.stdout
