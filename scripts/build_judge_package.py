from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import venv
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


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def verify_checkout_import(python: Path, checkout: Path) -> dict[str, object]:
    code = "from pathlib import Path; import sentinel_edge; print(Path(sentinel_edge.__file__).resolve())"
    proc = subprocess.run([str(python), "-c", code], cwd=checkout, text=True, capture_output=True, check=False)
    observed = proc.stdout.strip()
    expected = (checkout / "src").resolve()
    valid = False
    try:
        valid = proc.returncode == 0 and Path(observed).resolve().is_relative_to(expected)
    except (OSError, ValueError):
        valid = False
    return {
        "status": "pass" if valid else "fail",
        "valid": valid,
        "exit_code": proc.returncode,
        "observed": observed or None,
        "expected_root": str(expected),
        "stderr_tail": proc.stderr[-2000:],
    }


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

    # Generate a fresh deterministic local scenario proof for the package.
    # This is explicitly simulated/fixture evidence and must never be presented
    # as physical-device performance. The canonical final Arm64 matrix remains
    # a separate release-admission requirement.
    scenario_proc = subprocess.run(
        [sys.executable, "scripts/dev.py", "scenario"],
        cwd=ROOT, text=True, capture_output=True,
    )
    scenario_dir = output / "provenance" / "scenario-runs"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario-command.log").write_text(
        scenario_proc.stdout + "\n--- stderr ---\n" + scenario_proc.stderr, encoding="utf-8"
    )
    if scenario_proc.returncode != 0:
        print("scenario proof generation failed", file=sys.stderr)
        print(scenario_proc.stderr, file=sys.stderr)
        return scenario_proc.returncode
    try:
        scenario_payload = json.loads(scenario_proc.stdout)
    except json.JSONDecodeError:
        print("scenario proof output was not valid JSON", file=sys.stderr)
        return 2
    (scenario_dir / "simultaneous-event-proof.json").write_text(
        json.dumps(scenario_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    generated_scenario_dir = ROOT / ".tmp" / "scenario-proof"
    for source_name, target_name in (("transcript.json", "simultaneous-event-transcript.json"), ("invariants.json", "simultaneous-event-invariants.json")):
        source = generated_scenario_dir / source_name
        if not source.is_file():
            print(f"missing generated scenario artifact: {source_name}", file=sys.stderr)
            return 2
        shutil.copy2(source, scenario_dir / target_name)
    if scenario_payload.get("all_invariants_passed") is not True:
        print("scenario proof invariants did not all pass", file=sys.stderr)
        return 2

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
            tmp_root = Path(tmp)
            unpacked = tmp_root / "repo"
            smoke_venv = tmp_root / "venv"
            shutil.copytree(output, unpacked)
            # Keep the package smoke test isolated from editable/PTH state in the
            # developer interpreter. The temporary venv inherits already
            # available packages but owns the checkout .pth written by setup.
            venv.EnvBuilder(with_pip=True, system_site_packages=True, clear=True).create(smoke_venv)
            smoke_python = _venv_python(smoke_venv)
            commands = ["setup", "doctor", "verify", "demo", "scenario", "benchmark-replay", "claims", "gates"]
            receipts: dict[str, object] = {}
            ok = True
            for name in commands:
                code, log = run([str(smoke_python), "scripts/dev.py", name], unpacked)
                receipts[name] = {"exit_code": code, "status": "pass" if code == 0 else "fail", "tail": log[-2000:]}
                ok = ok and code == 0
                if name == "setup":
                    import_receipt = verify_checkout_import(smoke_python, unpacked)
                    receipts["checkout_import"] = import_receipt
                    ok = ok and bool(import_receipt.get("valid"))
            verification = {
                "status": "pass" if ok else "fail",
                "commands": receipts,
                "isolated_venv": True,
                "python": str(smoke_python),
            }

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
