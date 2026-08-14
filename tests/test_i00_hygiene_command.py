from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dev_command_surface_contains_fail_closed_hygiene_lane() -> None:
    text = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    assert '"hygiene"' in text
    assert 'repository_hygiene.py", "--check"' in text
