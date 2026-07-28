from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
from typing import Any

from _repo import ROOT, repo_path, sha256_file


def file_record(value: str) -> dict[str, str]:
    path = repo_path(value)
    if not path.is_file():
        raise FileNotFoundError(value)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--result", choices=("passed", "failed", "blocked"), required=True)
    parser.add_argument("--duration-seconds", type=float, required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--output-dir", default="provenance/evidence")
    parser.add_argument("--passed", type=int, default=0)
    args = parser.parse_args()
    payload: dict[str, Any] = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": args.command,
        "revision": args.revision,
        "environment": {"name": args.environment, "python": platform.python_version(), "platform": platform.platform()},
        "inputs": [file_record(value) for value in args.input],
        "result": args.result,
        "duration_seconds": args.duration_seconds,
        "artifacts": [file_record(value) for value in args.artifact],
        "counts": {"passed": args.passed, "failed": 0, "skipped": 0, "xfailed": 0, "rerun": 0, "collection_errors": 0},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    evidence_id = hashlib.sha256(canonical).hexdigest()
    payload["evidence_id"] = evidence_id
    target_dir = repo_path(args.output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{evidence_id}.json"
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        with target.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
    except FileExistsError:
        if target.read_text(encoding="utf-8") != serialized:
            raise RuntimeError(f"immutable evidence collision: {target}")
    print(target.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
