from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exported_tree_passes_hygiene_validation() -> None:
    output = ROOT / ".tmp" / "i00-clean-export"
    exported = subprocess.run([sys.executable, "scripts/export_source.py", "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
    assert exported.returncode == 0, exported.stdout + exported.stderr
    hygiene = subprocess.run([sys.executable, "scripts/repository_hygiene.py", "--check", "--root", str(output)], cwd=ROOT, text=True, capture_output=True)
    assert hygiene.returncode == 0, hygiene.stdout + hygiene.stderr
    manifest = json.loads((output / "source-export-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "sentinel-edge.source-export.v1"
    assert all(entry["class"] in {"source", "generated-contract", "evidence-input", "release-output"} for entry in manifest["files"])
    assert not any("__pycache__" in entry["path"] or entry["path"].startswith(".idea/") for entry in manifest["files"])
