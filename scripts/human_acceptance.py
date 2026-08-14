from __future__ import annotations

"""Run the deterministic portion of the Sentinel Edge human acceptance plan.

The acceptance document intentionally contains visual, keyboard and optional live
Gmail checks that cannot be honestly inferred by a command-line process. This
runner executes every bounded local/Arm64 proof available in the repository and
records those residual checks explicitly instead of silently treating them as
passed.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from sentinel_edge.release.submission import source_tree_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "qualification/human-acceptance.json"
LOG_DIR = ROOT / ".tmp/human-acceptance"

REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "CHANGELOG.md",
    "HACKATHON_WORKLOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "scripts/dev.py",
    "requirements-dev.lock.txt",
    "requirements-release.lock.json",
    "docs/judge-guide.md",
    "docs/release/CURRENT_SUBMISSION_READINESS.md",
    "docs/submission/DEVPOST_SUBMISSION.md",
    "docs/submission/VIDEO_SCRIPT.md",
    "docs/submission/VIDEO_SHOT_LIST.md",
    "docs/submission/VIDEO_OVERLAYS.md",
    "THIRD_PARTY_NOTICES.md",
)

UI_ROUTES = (
    "overview",
    "mission-control",
    "sites",
    "devices",
    "sensors",
    "cameras",
    "incidents",
    "investigation",
    "alerts",
    "dashboards",
    "reports",
    "policies",
    "automation",
    "firmware",
    "provisioning",
    "integrations",
    "collaboration",
    "benchmark",
    "judge-proof",
    "administration",
)

FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"(?i)(gmail|smtp|oauth|api)[_-]?(token|password|secret)\s*[:=]\s*[^\s]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def git_snapshot() -> dict[str, Any]:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True).splitlines()
    return {"branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(), "revision": revision, "clean": not status, "status": status}


def run_command(name: str) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc)
    proc = subprocess.run([sys.executable, "scripts/dev.py", name], cwd=ROOT, text=True, capture_output=True)
    log = LOG_DIR / f"{name}.log"
    log.write_text(f"$ {' '.join([sys.executable, 'scripts/dev.py', name])}\n\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n", encoding="utf-8", newline="\n")
    return {"status": "pass" if proc.returncode == 0 else "fail", "exit_code": proc.returncode, "log": log.relative_to(ROOT).as_posix(), "started_at": started.isoformat().replace("+00:00", "Z")}


def static_checks() -> dict[str, Any]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing:{relative}")
    app = (ROOT / "src/sentinel_edge/clients/static/app.js").read_text(encoding="utf-8")
    index = (ROOT / "src/sentinel_edge/clients/static/index.html").read_text(encoding="utf-8")
    for route in UI_ROUTES:
        if route not in app:
            failures.append(f"ui_route_missing:{route}")
    for required_text in ("Wildfire", "Earthquake", "Flood", "Landslide", "Research MVP", "Arm64 emulated", "monitoring coverage", "Collaborative Detection"):
        if required_text.lower() not in (app + index).lower():
            failures.append(f"ui_disclosure_or_hazard_missing:{required_text}")
    for path in (ROOT / "src", ROOT / "scripts", ROOT / "config", ROOT / "architecture"):
        for candidate in path.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in {".py", ".json", ".yaml", ".yml", ".md", ".toml"}:
                continue
            try:
                text = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in FORBIDDEN_SECRET_PATTERNS:
                if pattern.search(text):
                    failures.append(f"possible_secret:{candidate.relative_to(ROOT).as_posix()}")
                    break
    report = ROOT / "qualification/uix-conformance.json"
    if not report.is_file() or json.loads(report.read_text(encoding="utf-8")).get("summary", {}).get("overall_status") != "pass":
        failures.append("uix_conformance_not_green")
    return {"status": "pass" if not failures else "fail", "failures": sorted(set(failures)), "route_count": len(UI_ROUTES)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Sentinel Edge human-release acceptance checks")
    parser.add_argument("--local-only", action="store_true", help="Skip Docker/QEMU Arm64 lanes")
    parser.add_argument("--with-release-preflight", action="store_true", help="Run the full release preflight after bounded checks")
    parser.add_argument("--allow-dirty", action="store_true", help="Record a diagnostic run without requiring a clean candidate")
    args = parser.parse_args()

    results: dict[str, Any] = {"static": static_checks(), "commands": {}, "manual_remaining": [
        "desktop/mobile visual comparison and keyboard-only UI walkthrough",
        "optional live Gmail transport, inbox inspection and outage/retry demonstration",
        "final screenshot/video capture, public repository publication and Devpost submission",
    ]}
    try:
        results["git"] = git_snapshot()
    except (OSError, subprocess.CalledProcessError) as exc:
        results["git"] = {"clean": False, "error": str(exc)}
    if not args.allow_dirty and results.get("git", {}).get("clean") is not True:
        results["commands"]["candidate-cleanliness"] = {"status": "fail", "reason": "candidate_worktree_dirty"}
    else:
        results["commands"]["candidate-cleanliness"] = {"status": "pass"}

    commands = ["setup", "doctor", "verify", "demo", "scenario", "benchmark-replay", "collaboration-check", "collaboration-demo", "collaboration-gmail-fixture", "uix", "clients", "test-all"]
    if not args.local_only:
        commands.extend(["arm64-setup", "arm64-doctor", "arm64-test", "arm64-demo", "arm64-scenario", "arm64-benchmark"])
    if args.with_release_preflight:
        commands.append("submission-preflight")
    for command in commands:
        results["commands"][command] = run_command(command)

    results["status"] = "pass" if results["static"]["status"] == "pass" and all(row.get("status") == "pass" for row in results["commands"].values()) else "fail"
    results["schema"] = "sentinel-edge.human-acceptance.v1"
    results["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    results["source_tree_digest"] = source_tree_digest(ROOT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": results["status"], "output": OUTPUT.relative_to(ROOT).as_posix(), "manual_remaining": len(results["manual_remaining"])}, sort_keys=True))
    return 0 if results["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
