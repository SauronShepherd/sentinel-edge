from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def catalog() -> list[dict[str, object]]:
    payload = yaml.safe_load((ROOT / "architecture/command-catalog.yaml").read_text(encoding="utf-8"))
    return [item for item in payload["commands"] if not item.get("internal", False)]


def test_every_catalogued_public_command_is_exposed_by_help():
    result = subprocess.run(
        [sys.executable, "scripts/dev.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for item in catalog():
        assert item["name"] in result.stdout


def test_unknown_command_fails_closed():
    result = subprocess.run(
        [sys.executable, "scripts/dev.py", "not-a-command"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_public_catalog_has_no_duplicate_names_and_has_no_empty_required_lanes():
    items = catalog()
    names = [str(item["name"]) for item in items]
    assert len(names) == len(set(names))
    assert all(item["empty_allowed"] is False for item in items if item["name"] != "test-arm")
    assert all(str(item["purpose"]).strip() for item in items)
