"""Create a deterministic, truthful remediation-baseline receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANDATORY_WORKFLOWS = ("ci-fast.yml", "ci-full.yml", "ci-release.yml")


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()


def repository_state() -> dict[str, object]:
    """Return truthful Git metadata without making source archives untestable.

    Final release admission still requires a real clean Git revision.  Baseline
    auditing, however, is also used by unpacked Judge/source archives where
    `.git` metadata is intentionally absent.
    """
    try:
        return {
            "git_available": True,
            "head": run("git", "rev-parse", "HEAD"),
            "branch": run("git", "branch", "--show-current"),
            "dirty": bool(run("git", "status", "--porcelain")),
            "remotes": run("git", "remote", "-v").splitlines(),
        }
    except (OSError, subprocess.CalledProcessError):
        return {
            "git_available": False,
            "head": None,
            "branch": None,
            "dirty": None,
            "remotes": [],
        }


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def inventory() -> list[str]:
    self_receipt = Path("provenance/evidence/remediation/R00/baseline-receipt.json")
    return sorted(
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in ROOT.rglob("*")
        if p.is_file()
        and ".git" not in p.relative_to(ROOT).parts
        and p.relative_to(ROOT).as_posix() != self_receipt.as_posix()
    )


def registry_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted((ROOT / "registries").glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        items = payload.get("items", []) if isinstance(payload, dict) else payload
        counts[path.name] = len(items) if isinstance(items, list) else 0
    return counts


def build_receipt() -> dict[str, object]:
    files = inventory()
    workflows = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / ".github/workflows").glob("*") if p.is_file()) if (ROOT / ".github/workflows").exists() else []
    return {
        "schema": "sentinel-edge.remediation-baseline.v1",
        "audit_date": "2026-08-04",
        "repository": repository_state(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "inventory": {"count": len(files), "sha256": digest(files)},
        "registry_counts": registry_counts(),
        "workflows": {"present": workflows, "missing": [f".github/workflows/{n}" for n in MANDATORY_WORKFLOWS if f".github/workflows/{n}" not in workflows]},
        "status_policy": {"verified_requires_receipt": True, "fixture_evidence_is_non_target": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "provenance/evidence/remediation/R00/baseline-receipt.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = build_receipt()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    if args.check and (receipt["repository"]["dirty"] is True or receipt["workflows"]["missing"]):
        print(json.dumps({"valid": False, "reasons": ["dirty_worktree_or_missing_workflows"]}, indent=2))
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
