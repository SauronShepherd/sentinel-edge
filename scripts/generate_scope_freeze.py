"""Generate the immutable development H0 scope-freeze projection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def generate(root: Path) -> dict[str, object]:
    path = root / "registries/requirements.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    requirements = payload.get("items", [])
    h0_ids = sorted(
        item["id"] for item in requirements if "profile H0" in item.get("statement", "")
    )
    return {
        "schema": "sentinel-edge.scope-freeze.v1",
        "freeze_id": "R00-H0-SCOPE-20260812",
        "frozen_at": "2026-08-12T00:00:00Z",
        "requirements_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "h0_ids_sha256": hashlib.sha256("\n".join(h0_ids).encode()).hexdigest(),
        "h0_count": len(h0_ids),
        "exceptions": [],
        "exception_schema": {
            "required_fields": ["exception_id", "reason", "approver", "displaced_or_cut", "affected_requirements", "mandatory_reruns"]
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "qualification/scope-freeze.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(generate(root), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"h0_count": generate(root)["h0_count"], "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
