from __future__ import annotations

"""Regenerate repository-bound release evidence before final candidate closure.

This script deliberately avoids target-only evidence that cannot be recreated in the
hackathon emulated-H0 profile. It refreshes source/dependency-bound artifacts whose
hashes become stale whenever repository code changes.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".tmp" / "privacy-closure-state"


def run(args: list[str]) -> dict[str, object]:
    command = [sys.executable, "-m", "sentinel_edge.cli", *args]
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    result = {
        "command": command,
        "exit_code": proc.returncode,
        "status": "pass" if proc.returncode == 0 else "fail",
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }
    if proc.returncode != 0:
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(proc.returncode)
    return result


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, object]] = []
    # Dependency identity first; downstream SBOM/provenance/reproducibility bind it.
    steps.append(run(["build-release-lock", "--root", "."]))
    steps.append(run(["build-sbom", "--root", "."]))
    steps.append(run(["build-third-party-inventory", "--root", "."]))
    steps.append(run(["build-third-party-notices", "--root", "."]))
    rights_proc = subprocess.run([sys.executable, "scripts/generate_rights_inventory.py"], cwd=ROOT, text=True, capture_output=True)
    rights_result = {
        "command": [sys.executable, "scripts/generate_rights_inventory.py"],
        "exit_code": rights_proc.returncode,
        "status": "pass" if rights_proc.returncode == 0 else "fail",
        "stdout": rights_proc.stdout.strip(),
        "stderr": rights_proc.stderr.strip(),
    }
    if rights_proc.returncode != 0:
        print(json.dumps(rights_result, indent=2, sort_keys=True))
        raise SystemExit(rights_proc.returncode)
    steps.append(rights_result)
    snapshots = [
        "fixtures/security/advisory-osv-bounded.json",
        "fixtures/security/advisory-github_advisory-bounded.json",
        "fixtures/security/advisory-cisa_kev-bounded.json",
        "fixtures/security/advisory-vendor-bounded.json",
    ]
    security_args = ["build-security-review", "--root", "."]
    for snapshot in snapshots:
        security_args.extend(["--snapshot", snapshot])
    steps.append(run(security_args))
    steps.append(run(["build-privacy-closure", "--root", ".", "--state-dir", str(STATE_DIR)]))
    # Reproducibility captures the final dependency lock and current source members.
    steps.append(run(["build-reproducibility-report", "--root", "."]))
    # Provenance must be last because it binds all non-generated repository materials.
    steps.append(run(["build-provenance", "--root", "."]))

    verification = [
        run(["verify-reproducibility-report", "reproducibility-report.json", "--root", "."]),
        run(["verify-provenance", "build-provenance.json", "--root", "."]),
        run(["verify-security-review", "security-review.json", "--sbom", "sbom.cdx.json"]),
        run(["verify-privacy-closure", "privacy-closure.json"]),
    ]
    payload = {
        "schema": "sentinel-edge.release-evidence-preparation.v1",
        "status": "pass",
        "steps": [{"command": item["command"], "status": item["status"]} for item in steps],
        "verification": [{"command": item["command"], "status": item["status"]} for item in verification],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
