from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_python_and_typescript_fixtures_preserve_canonical_json():
    fixture = {
        "observation_id": "obs-1",
        "observed_at": "2026-01-01T00:00:00Z",
        "units": "metric",
        "clock_quality": "trusted",
        "replay": False,
        "policy": {"retention": "public"},
        "source_health": {},
        "acquisition_audit": {},
    }
    encoded = json.dumps(fixture, sort_keys=True, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert json.dumps(decoded, sort_keys=True, separators=(",", ":")) == encoded
    result = subprocess.run(
        ["node", "--test", "test/contract-roundtrip.test.mjs"],
        cwd=ROOT / "modules/client-applications",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
