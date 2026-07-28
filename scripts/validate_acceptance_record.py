from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from _repo import ROOT, load_json, repo_path, sha256_file


def validate(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("schema_version", "iteration", "status", "candidate_revision", "stages", "mandatory_commands", "test_counts"):
        if field not in record:
            errors.append(f"missing field: {field}")
    counts = record.get("test_counts", {})
    for field in ("failed", "skipped", "xfailed", "rerun", "collection_errors"):
        if counts.get(field, 0) != 0:
            errors.append(f"non-zero {field}: {counts.get(field)}")
    if record.get("status") == "complete":
        if not record.get("accepted_at"):
            errors.append("complete record lacks accepted_at")
        stages = record.get("stages", {})
        if not stages or any(value != "complete" for value in stages.values()):
            errors.append("complete record contains incomplete stage")
        evidence = record.get("evidence", [])
        if not evidence:
            errors.append("complete record lacks evidence")
        for item in evidence:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                errors.append(f"invalid evidence entry: {item!r}")
                continue
            path = repo_path(item["path"])
            if not path.is_file():
                errors.append(f"missing evidence file: {item['path']}")
                continue
            if item.get("sha256") != sha256_file(path):
                errors.append(f"stale evidence hash: {item['path']}")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_acceptance_record.py PATH")
        return 2
    path = Path(sys.argv[1])
    record = load_json(path)
    errors = validate(record)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"acceptance record: PASS ({record.get('iteration')} {record.get('status')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
