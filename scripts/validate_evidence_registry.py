"""Validate the canonical evidence registry without upgrading claims.

Historical evidence may be externalized from this checkout. Such records are
reported as unavailable; only malformed records, duplicate identities, unsafe
paths, or digest mismatches for locally available files fail validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id", "kind", "summary", "path", "sha256", "captured_at", "producer", "status"}
SHA256_HEX_LENGTH = 64


def validate(root: Path) -> dict[str, object]:
    registry_path = root / "registries/evidence.yaml"
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    items = payload.get("items", [])
    failures: list[str] = []
    unavailable: list[str] = []
    local_available = 0
    ids: set[str] = set()
    paths: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"item[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{prefix}:not_an_object")
            continue
        missing = REQUIRED - set(item)
        failures.extend(f"{prefix}:missing:{field}" for field in sorted(missing))
        record_id = item.get("id")
        path_value = item.get("path")
        if isinstance(record_id, str):
            if record_id in ids:
                failures.append(f"duplicate_id:{record_id}")
            ids.add(record_id)
        if not isinstance(path_value, str):
            continue
        normalized = PurePosixPath(path_value)
        if normalized.is_absolute() or ".." in normalized.parts or "://" in path_value or not path_value.strip():
            failures.append(f"unsafe_path:{record_id or prefix}")
            continue
        normalized_path = normalized.as_posix()
        if normalized_path in paths:
            failures.append(f"duplicate_path:{normalized_path}")
        paths.add(normalized_path)
        digest = item.get("sha256")
        if not isinstance(digest, str) or len(digest) != SHA256_HEX_LENGTH:
            failures.append(f"invalid_sha256:{record_id or prefix}")
        elif any(char not in "0123456789abcdef" for char in digest.lower()):
            failures.append(f"invalid_sha256:{record_id or prefix}")
        local_path = (root / normalized_path).resolve()
        try:
            local_path.relative_to(root.resolve())
        except ValueError:
            failures.append(f"resolved_path_outside_root:{record_id or prefix}")
            continue
        if not local_path.is_file():
            unavailable.append(record_id or prefix)
        else:
            local_available += 1
            if isinstance(digest, str) and hashlib.sha256(local_path.read_bytes()).hexdigest() != digest:
                failures.append(f"digest_mismatch:{record_id or prefix}")
    return {
        "valid": not failures,
        "count": len(items) if isinstance(items, list) else 0,
        "local_available": local_available,
        "unavailable": unavailable,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict-local", action="store_true")
    args = parser.parse_args()
    result = validate(args.root.resolve())
    if args.strict_local and result["unavailable"]:
        result["valid"] = False
        result["failures"] = [*result["failures"], f"unavailable_local_evidence:{len(result['unavailable'])}"]
    display = dict(result)
    unavailable = display.pop("unavailable", [])
    display["unavailable_count"] = len(unavailable)
    print(json.dumps(display, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
