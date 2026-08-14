from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_source
import repository_hygiene


def test_export_allowlist_excludes_generated_state() -> None:
    assert export_source.allowed(ROOT / "src/sentinel_edge/__init__.py")
    assert not export_source.allowed(ROOT / "src/sentinel_edge/__pycache__/module.pyc")
    assert not export_source.allowed(ROOT / ".idea/workspace.xml")


def test_hygiene_reports_generated_state_without_treating_git_as_source() -> None:
    violations = repository_hygiene.violations()
    assert not any(path == ".git" or path.startswith(".git/") for path in violations)
