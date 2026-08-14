"""Generate the deterministic v0.22 active-contract identity snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / ".tmp" / "active-contract-snapshot.json")
    parser.add_argument("--profile", default="H0")
    args = parser.parse_args()
    root = args.root.resolve()
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    registries = {}
    for name in ("requirements.yaml", "tasks.yaml", "tests.yaml", "iterations.yaml"):
        path = root / "registries" / name
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        registries[name] = {"count": len(payload.get("items", [])), "sha256": sha256(path)}
    contracts = {}
    for path in sorted((root / "docs/contracts").glob("*v0.22.0.md")):
        contracts[path.name] = sha256(path)
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "git_metadata_unavailable"
    snapshot = {
        "schema": "sentinel-edge.active-contract-snapshot.v1",
        "implementation_version": project["version"],
        "contract_version": "0.22.0",
        "profile": args.profile,
        "source_revision": revision,
        "contracts": contracts,
        "registries": registries,
        "release_claims": {"release_admitted": False, "target_qualified": False, "independent_review_complete": False},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(snapshot, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
