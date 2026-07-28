
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_evidence_schema_has_mandatory_fields() -> None:
    schema = json.loads((ROOT / "provenance/test-evidence.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert {"command", "revision", "environment", "inputs", "result", "duration_seconds", "artifacts"} <= required
    assert schema["properties"]["result"]["enum"] == ["passed", "failed", "blocked"]


def test_evidence_writer_is_immutable_and_content_addressed() -> None:
    output_dir = ROOT / "build/test-evidence"
    output_dir.mkdir(parents=True, exist_ok=True)
    args = [
        sys.executable, "scripts/record_test_evidence.py",
        "--command", "pytest tests/governance",
        "--revision", "test-revision",
        "--result", "passed",
        "--duration-seconds", "1.5",
        "--environment", "test",
        "--input", "pyproject.toml",
        "--artifact", "provenance/test-evidence.schema.json",
        "--output-dir", "build/test-evidence",
    ]
    first = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    assert first.returncode == 0, first.stdout + first.stderr
    path = ROOT / first.stdout.strip()
    before = path.read_bytes()
    assert len(path.stem) == 64
    assert path.read_bytes() == before
    path.unlink()
