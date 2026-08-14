from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_source


def test_allowlist_accepts_posix_and_windows_style_root_entries() -> None:
    assert export_source.allowed(ROOT / "src" / "sentinel_edge" / "__init__.py")
    assert export_source.allowed(ROOT / "docs" / "README.md")
    assert export_source.allowed(ROOT / "docker" / "Dockerfile.arm64")
    assert export_source.allowed(ROOT / "schemas" / "collaborative-signal-v1.schema.json")
    assert export_source.allowed(ROOT / "requirements-dev.lock.txt")
    assert export_source.allowed(ROOT / "requirements-bootstrap.lock.txt")
    assert export_source.allowed(ROOT / "HACKATHON_WORKLOG.md")
    assert export_source.allowed(ROOT / "SECURITY.md")
    assert export_source.allowed(ROOT / "CONTRIBUTING.md")


def test_allowlist_rejects_path_outside_repository() -> None:
    assert not export_source.allowed(Path(ROOT.drive + "\\outside"))
