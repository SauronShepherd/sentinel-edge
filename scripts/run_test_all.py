from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from sentinel_edge.release.submission import source_tree_digest


ROOT = Path(__file__).resolve().parents[1]


def batches(items: list[Path], size: int) -> list[list[Path]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _setup_environment_fingerprint() -> dict[str, Any]:
    path = ROOT / ".tmp/setup-environment.json"
    if not path.is_file():
        return {"present": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"present": True, "valid": False}
    exact_rows = payload.get("exact_requirements", [])
    return {
        "present": True,
        "valid": payload.get("status") == "pass",
        "python": payload.get("python"),
        "python_executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "mode": payload.get("mode"),
        "exact_locked": payload.get("exact_locked"),
        "requirements": [
            {"name": row.get("name"), "expected": row.get("expected"), "actual": row.get("actual")}
            for row in exact_rows if isinstance(row, dict)
        ],
    }


def _digest(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _valid_reusable_receipt(path: Path, *, source_digest: str, environment_digest: str, signature: str, paths: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("valid") is not True:
        return None
    if payload.get("source_tree_digest") != source_digest or payload.get("environment_digest") != environment_digest:
        return None
    if payload.get("batch_signature") != signature or payload.get("paths") != paths:
        return None
    if int(payload.get("collected", 0) or 0) <= 0:
        return None
    if payload.get("skipped") or payload.get("xfail_or_xpass") or payload.get("failed"):
        return None
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete Sentinel Edge test tree in strict bounded batches")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--resume", action="store_true", help="Reuse only exact-source/exact-environment valid batch receipts")
    args = parser.parse_args()
    if args.batch_size <= 0:
        raise SystemExit("batch-size must be positive")

    tests = sorted(path.relative_to(ROOT) for path in (ROOT / "tests").rglob("test_*.py") if path.is_file())
    if not tests:
        print("test-all: FAIL (zero test files discovered)")
        return 1

    started = time.monotonic()
    output = ROOT / ".tmp" / "test-all"
    groups = batches(tests, args.batch_size)
    source_digest = source_tree_digest(ROOT)
    environment = _setup_environment_fingerprint()
    environment_digest = _digest(environment)
    plan = {
        "schema": "sentinel-edge.test-all-plan.v1",
        "source_tree_digest": source_digest,
        "environment": environment,
        "environment_digest": environment_digest,
        "batch_size": args.batch_size,
        "test_files": [path.as_posix() for path in tests],
        "batch_count": len(groups),
    }
    plan_path = output / "plan.json"
    resumable = False
    if args.resume and plan_path.is_file():
        try:
            resumable = json.loads(plan_path.read_text(encoding="utf-8")) == plan
        except (OSError, json.JSONDecodeError):
            resumable = False
    if output.exists() and not resumable:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    receipts: list[dict[str, Any]] = []
    reused_batches = 0
    for index, group in enumerate(groups, start=1):
        group_paths = [path.as_posix() for path in group]
        signature = _digest({"source_tree_digest": source_digest, "environment_digest": environment_digest, "paths": group_paths})
        receipt_path = output / f"batch-{index:02d}.json"
        reused = _valid_reusable_receipt(
            receipt_path, source_digest=source_digest, environment_digest=environment_digest,
            signature=signature, paths=group_paths,
        ) if resumable else None
        if reused is not None:
            receipts.append(reused)
            reused_batches += 1
            print(f"test-all: batch {index}/{len(groups)} reused ({len(group)} files)", flush=True)
            continue
        print(f"test-all: batch {index}/{len(groups)} ({len(group)} files)", flush=True)
        command = [
            sys.executable,
            "scripts/run_pytest_acceptance_batch.py",
            "--receipt", str(receipt_path),
            "--source-tree-digest", source_digest,
            "--environment-digest", environment_digest,
            "--batch-signature", signature,
            "--batch-index", str(index),
            *group_paths,
        ]
        completed = subprocess.run(command, cwd=ROOT, check=False)
        if receipt_path.is_file():
            receipts.append(json.loads(receipt_path.read_text(encoding="utf-8")))
        if completed.returncode != 0:
            summary = {
                "schema": "sentinel-edge.test-all.v1",
                "valid": False,
                "test_files": len(tests),
                "batch_count": len(groups),
                "completed_batches": len(receipts),
                "reused_batches": reused_batches,
                "source_tree_digest": source_digest,
                "environment_digest": environment_digest,
                "collected": sum(int(item.get("collected", 0)) for item in receipts),
                "failed_batch": index,
                "duration_seconds": round(time.monotonic() - started, 3),
                "evidence_dir": output.relative_to(ROOT).as_posix(),
            }
            (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"test-all: FAIL in batch {index}")
            return completed.returncode

    summary = {
        "schema": "sentinel-edge.test-all.v1",
        "valid": bool(receipts) and all(bool(item.get("valid")) for item in receipts),
        "test_files": len(tests),
        "batch_count": len(groups),
        "completed_batches": len(receipts),
        "reused_batches": reused_batches,
        "source_tree_digest": source_digest,
        "environment_digest": environment_digest,
        "collected": sum(int(item.get("collected", 0)) for item in receipts),
        "skipped": sum(len(item.get("skipped", [])) for item in receipts),
        "xfail_or_xpass": sum(len(item.get("xfail_or_xpass", [])) for item in receipts),
        "duration_seconds": round(time.monotonic() - started, 3),
        "evidence_dir": output.relative_to(ROOT).as_posix(),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not summary["valid"] or summary["collected"] <= 0:
        print("test-all: FAIL (strict acceptance summary invalid)")
        return 1
    print(f"test-all: PASS ({summary['collected']} tests across {summary['test_files']} files; no skips/xfails)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
