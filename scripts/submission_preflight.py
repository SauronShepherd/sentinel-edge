from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from sentinel_edge.release.submission import RELEASE_GENERATED_FILES, REQUIRED_ARM64_COMMANDS, REQUIRED_LOCAL_COMMANDS, source_tree_digest

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / ".tmp/submission-preflight"
OUTPUT = ROOT / "qualification/submission-command-matrix.json"


def git_state() -> dict[str, object]:
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
        raw_status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True, stderr=subprocess.STDOUT).splitlines()
        status: list[str] = []
        for entry in raw_status:
            path_text = entry[3:] if len(entry) > 3 else entry
            if " -> " in path_text:
                path_text = path_text.split(" -> ", 1)[1]
            if path_text.replace("\\", "/") in RELEASE_GENERATED_FILES:
                continue
            status.append(entry)
        return {"git_available": True, "revision": revision, "dirty": bool(status), "status_entries": status}
    except (OSError, subprocess.CalledProcessError):
        return {"git_available": False, "revision": None, "dirty": None, "status_entries": []}


def run_command(name: str) -> dict[str, object]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "scripts/dev.py", name]
    started = dt.datetime.now(dt.timezone.utc)
    monotonic_start = time.monotonic()
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=os.environ.copy())
    finished = dt.datetime.now(dt.timezone.utc)
    duration = time.monotonic() - monotonic_start
    log_path = LOG_DIR / f"{name}.log"
    log_path.write_text(
        f"$ {' '.join(command)}\n\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "exit_code": proc.returncode,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "duration_seconds": round(duration, 3),
        "python": sys.version.split()[0],
        "host_platform": platform.platform(),
        "log": log_path.relative_to(ROOT).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true", help="Run only the host Judge path; never release-admissible.")
    args = parser.parse_args()
    repository = git_state()
    commands: dict[str, dict[str, object]] = {}
    for name in REQUIRED_LOCAL_COMMANDS:
        commands[name] = run_command(name)
        if commands[name]["status"] != "pass":
            # Continue to provide a complete diagnostic matrix where possible.
            pass
    if args.local_only:
        for name in REQUIRED_ARM64_COMMANDS:
            commands[name] = {"status": "not_run", "exit_code": 2, "reason": "local_only_preflight"}
    else:
        for name in REQUIRED_ARM64_COMMANDS:
            commands[name] = run_command(name)

    required = (*REQUIRED_LOCAL_COMMANDS, *REQUIRED_ARM64_COMMANDS)
    repository_clean = repository.get("git_available") is True and repository.get("dirty") is False and bool(repository.get("revision"))
    overall_pass = all(commands.get(name, {}).get("status") == "pass" for name in required) and repository_clean
    evidence_preparation: dict[str, object] = {"status": "not_run", "exit_code": 2}
    if overall_pass:
        proc = subprocess.run([sys.executable, "scripts/prepare_release_evidence.py"], cwd=ROOT, text=True, capture_output=True, env=os.environ.copy())
        evidence_preparation = {
            "status": "pass" if proc.returncode == 0 else "fail",
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
        overall_pass = overall_pass and proc.returncode == 0
    payload = {
        "schema": "sentinel-edge.submission-command-matrix.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_profile": "H0-EMULATED-AARCH64-20260813",
        "source_tree_digest": source_tree_digest(ROOT),
        "repository": repository,
        "commands": commands,
        "release_evidence_preparation": evidence_preparation,
        "required_local_commands": list(REQUIRED_LOCAL_COMMANDS),
        "required_arm64_commands": list(REQUIRED_ARM64_COMMANDS),
        "overall_status": "pass" if overall_pass else "fail",
        "physical_hardware_required": False,
        "physical_sensors_required": False,
        "raspberry_pi_performance_claim_allowed": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if overall_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
