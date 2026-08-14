from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist/judge-package"
ROOT_EVIDENCE = (
    "NOTICE",
    "sbom.cdx.json",
    "third-party-inventory.json",
    "requirements-release.lock.json",
    "build-provenance.json",
    "security-review.json",
    "privacy-closure.json",
    "reproducibility-report.json",
    "host-trust-report.json",
    "network-isolation-report.json",
    "independent-build-report.json",
    "release-governance-report.json",
    "power-energy-report.json",
    "runtime-known-issue-report.json",
    "benchmark-analysis-report.json",
    "release-candidate.json",
    "release-manifest.json",
    "release-candidate.json.sig.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return proc.returncode, (proc.stdout + "\n" + proc.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-local", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    export = subprocess.run(
        [sys.executable, "scripts/export_source.py", "--root", str(ROOT), "--output", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if export.returncode != 0:
        print(export.stdout)
        print(export.stderr, file=sys.stderr)
        return export.returncode

    for name in ROOT_EVIDENCE:
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, output / name)

    manifest_records = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "judge-package-manifest.json":
            manifest_records.append({
                "path": path.relative_to(output).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    candidate = {}
    try:
        candidate = json.loads((output / "release-candidate.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    manifest = {
        "schema": "sentinel-edge.judge-package.v1",
        "candidate_id": candidate.get("candidate_id"),
        "release_profile": candidate.get("release_profile") or "H0-EMULATED-AARCH64-20260813",
        "release_admitted": bool(candidate.get("release_admitted", False)),
        "files": manifest_records,
    }
    manifest_path = output / "judge-package-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    verification: dict[str, object] = {"status": "not_requested"}
    if args.verify_local:
        with tempfile.TemporaryDirectory(prefix="sentinel-judge-package-") as tmp:
            unpacked = Path(tmp) / "repo"
            shutil.copytree(output, unpacked)
            commands = ["setup", "doctor", "verify", "demo", "scenario", "benchmark-replay", "claims", "gates"]
            receipts = {}
            ok = True
            for name in commands:
                code, log = run([sys.executable, "scripts/dev.py", name], unpacked)
                receipts[name] = {"exit_code": code, "status": "pass" if code == 0 else "fail", "tail": log[-2000:]}
                ok = ok and code == 0
            verification = {"status": "pass" if ok else "fail", "commands": receipts}

    result = {
        "output": str(output),
        "files": len(manifest_records),
        "manifest_sha256": sha256(manifest_path),
        "release_admitted": manifest["release_admitted"],
        "verification": verification,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if verification.get("status") != "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
