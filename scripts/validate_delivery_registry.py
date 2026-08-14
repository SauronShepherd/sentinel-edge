"""Validate the canonical Sentinel Edge task/test/iteration delivery registries."""

from __future__ import annotations

import argparse
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"PLANNED", "IN_PROGRESS", "PASSED", "VERIFIED", "MERGED", "BLOCKED", "RETIRED"}


def load(root: Path, name: str) -> list[dict]:
    payload = yaml.safe_load((root / "registries" / name).read_text(encoding="utf-8"))
    return payload.get("items", [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    tasks = load(args.root, "tasks.yaml")
    tests = load(args.root, "tests.yaml")
    iterations = load(args.root, "iterations.yaml")
    failures: list[str] = []
    for label, rows in (("task", tasks), ("test", tests), ("iteration", iterations)):
        ids = [row.get("id") for row in rows]
        if any(not value for value in ids) or len(ids) != len(set(ids)):
            failures.append(f"{label}_ids_missing_or_duplicate")
        for row in rows:
            if row.get("status") not in ALLOWED:
                failures.append(f"{label}_invalid_status:{row.get('id')}:{row.get('status')}")
            if row.get("status") == "VERIFIED" and not row.get("completion_execution_id"):
                failures.append(f"{label}_verified_without_execution:{row.get('id')}")
    iteration_ids = {row.get("id") for row in iterations}
    for task in tasks:
        if task.get("iteration_id") not in iteration_ids:
            failures.append(f"task_iteration_missing:{task.get('id')}")
    result = {"valid": not failures, "counts": {"tasks": len(tasks), "tests": len(tests), "iterations": len(iterations)}, "failures": failures}
    print(yaml.safe_dump(result, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
