from __future__ import annotations
import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ARM64_IMAGE = "sentinel-edge:arm64-emulated"


def load_command_catalog() -> list[dict[str, object]]:
    payload = yaml.safe_load((ROOT / "architecture/command-catalog.yaml").read_text(encoding="utf-8")) or {}
    commands = payload.get("commands", [])
    if not isinstance(commands, list):
        raise SystemExit("command_catalog_invalid:commands_not_a_list")
    return commands


COMMAND_CATALOG = load_command_catalog()
COMMANDS = tuple(str(item["name"]) for item in COMMAND_CATALOG if not item.get("internal", False))
INTERNAL_COMMANDS = tuple(str(item["name"]) for item in COMMAND_CATALOG if item.get("internal", False))


WORKSTREAM_TESTS = {
    1: [
        "tests/test_architecture.py",
        "tests/test_contracts.py",
        "tests/test_qualification.py",
    ],
}

def run(command: list[str]) -> int:
    return subprocess.call(command)


def run_arm64(*args: str, build: bool = False) -> int:
    """Run one project command in the canonical Docker/QEMU AArch64 guest."""
    if shutil.which("docker") is None:
        print("arm64 emulation unavailable: docker executable not found")
        return 2
    if build:
        image_present = subprocess.run(
            ["docker", "image", "inspect", ARM64_IMAGE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if not image_present:
            result = run(["docker", "build", "--platform", "linux/arm64", "-f", "docker/Dockerfile.arm64", "-t", ARM64_IMAGE, "."])
            if result:
                return result
        else:
            print(f"reusing verified Arm64 image: {ARM64_IMAGE}")
    return run(["docker", "run", "--rm", "--platform", "linux/arm64", "-e", f"SENTINEL_HOST_ARCH={platform.machine()}", "-v", f"{ROOT}:/workspace", "-w", "/workspace", ARM64_IMAGE, "python", *args])


def run_lane(*commands: list[str]) -> int:
    for command in commands:
        result = run(command)
        if result:
            return result
    return 0


def mandatory_test_command(paths: list[str]) -> list[str]:
    """Build a fail-closed pytest command for an active mandatory lane."""
    if not paths:
        raise ValueError("mandatory test lane cannot be empty")
    return [sys.executable, "-m", "pytest", "-q", *paths]


def fresh_state(path: str) -> str:
    target = Path(path)
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    work = sub.add_parser("test-workstream")
    work.add_argument("section", type=int)
    e2e = sub.add_parser("e2e-iteration")
    e2e.add_argument("iteration", type=int)
    for command in COMMANDS:
        sub.add_parser(command)
    args = parser.parse_args()
    if args.command == "test-workstream":
        selected = WORKSTREAM_TESTS.get(args.section)
        if selected is None:
            raise SystemExit(f"No bounded test selection is declared for workstream {args.section}")
        try:
            command = mandatory_test_command(selected)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        raise SystemExit(run(command))
    if args.command == "test-all":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q"]))
    if args.command == "arm64-setup":
        raise SystemExit(run_arm64("--help", build=True))
    if args.command == "arm64-doctor":
        raise SystemExit(run_arm64("scripts/arm64_doctor.py", build=False))
    if args.command == "arm64-test":
        raise SystemExit(run_arm64(
            "-m", "pytest", "-q",
            "tests/test_architecture.py",
            "tests/test_scheduler.py",
            "tests/test_scenario_e2e.py",
            "tests/test_scenario_faults.py",
            "tests/test_earthquake_hard_negatives.py",
            "tests/test_flood_landslide_contracts.py",
            "tests/test_benchmark_lab.py",
            "tests/test_collaboration_contracts.py",
            build=False,
        ))
    if args.command == "arm64-demo":
        raise SystemExit(run_arm64("scripts/dev.py", "demo", build=False))
    if args.command == "arm64-scenario":
        raise SystemExit(run_arm64("scripts/dev.py", "scenario", build=False))
    if args.command == "arm64-benchmark":
        raise SystemExit(run_arm64("scripts/run_emulated_benchmark.py", build=False))
    if args.command == "collaboration-check":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_collaboration_contracts.py"]))
    if args.command == "test-collaboration":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_collaboration_contracts.py"]))
    if args.command == "collaboration-demo":
        from sentinel_edge.collaboration import run_demo
        import json
        print(json.dumps(run_demo(), sort_keys=True))
        raise SystemExit(0)
    if args.command == "collaboration-gmail-fixture":
        raise SystemExit(run([sys.executable, "scripts/run_collaboration_gmail_fixture.py"]))
    if args.command == "submission-preflight":
        raise SystemExit(run([sys.executable, "scripts/submission_preflight.py"]))
    if args.command == "release-candidate":
        preflight = run([sys.executable, "scripts/verify_submission_preflight.py"])
        if preflight:
            raise SystemExit(preflight)
        state_dir = fresh_state(".tmp/release-candidate-state")
        build = run([sys.executable, "-m", "sentinel_edge.cli", "build-release-candidate", "--root", ".", "--state-dir", state_dir])
        if build:
            raise SystemExit(build)
        verify_result = run([sys.executable, "-m", "sentinel_edge.cli", "verify-release-candidate", "release-candidate.json", "--root", "."] )
        run([sys.executable, "scripts/generate_submission_readiness.py"])
        if verify_result:
            raise SystemExit(verify_result)
        raise SystemExit(run([sys.executable, "scripts/verify_release_admission.py"]))
    if args.command == "plugins":
        raise SystemExit(run([sys.executable, "scripts/run_capability_lane.py", "plugins"]))
    if args.command == "testkit":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/contracts"]))
    if args.command == "components":
        raise SystemExit(run([sys.executable, "scripts/run_capability_lane.py", "components"]))
    if args.command == "clients":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/check_client_boundaries.py"],
            [sys.executable, "-m", "pytest", "-q", "tests/test_client_security.py"],
        ))
    if args.command == "packages":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/check_version_consistency.py"],
            [sys.executable, "scripts/check_lock_metadata.py"],
            [sys.executable, "scripts/repository_hygiene.py", "--check"],
        ))
    if args.command == "compatibility":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/check_compatibility.py"],
            [sys.executable, "-m", "pytest", "-q", "tests/contracts"],
        ))
    if args.command == "generated":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/generate_contracts.py"],
            [sys.executable, "-m", "pytest", "-q", "tests/contracts"],
        ))
    if args.command == "security":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/run_capability_lane.py", "security"],
            [sys.executable, "-m", "pytest", "-q", "tests/test_auth_and_commands.py", "tests/test_client_security.py"],
        ))
    if args.command == "privacy":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/run_capability_lane.py", "privacy"],
            [sys.executable, "-m", "pytest", "-q", "tests/test_privacy_closure.py", "tests/test_privacy_backup_and_exports.py"],
        ))
    if args.command == "accessibility":
        raise SystemExit(run([sys.executable, "scripts/run_capability_lane.py", "accessibility"]))
    if args.command == "provenance":
        raise SystemExit(run_lane(
            [sys.executable, "-m", "pytest", "-q", "tests/test_provenance_and_advisories.py"],
            [sys.executable, "scripts/check_lock_metadata.py"],
        ))
    if args.command == "docs":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/check_markdown_links.py"],
            [sys.executable, "scripts/check_contract_sync.py"],
        ))
    if args.command == "report":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/generate_claim_registry.py"],
            [sys.executable, "scripts/validate_claim_registry.py"],
            [sys.executable, "scripts/generate_conformance_ledger.py"],
            [sys.executable, "scripts/generate_release_minimum_manifest.py"],
            [sys.executable, "scripts/generate_submission_readiness.py"],
        ))
    if args.command == "package":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/repository_hygiene.py", "--check"],
            [sys.executable, "scripts/check_lock_metadata.py"],
            [sys.executable, "scripts/build_judge_package.py"],
        ))
    if args.command == "backup-verify":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_storage_backup_and_spool.py", "tests/test_privacy_backup_and_exports.py"]))
    if args.command == "update-verify":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_offline_updates.py", "tests/test_update_tombstone_binding.py"]))
    if args.command == "test-arm":
        # The workflow is intentionally a preflight only: it must inspect the
        # host and expose qualification truth without turning a development
        # host or fixture into target benchmark evidence.
        print("Arm target preflight: running deterministic doctor inspection.")
        result = run([sys.executable, "-m", "sentinel_edge.cli", "doctor"])
        if result:
            raise SystemExit(result)
        print("Arm benchmark capability remains planned; this lane is not benchmark evidence.")
        raise SystemExit(0)
    if args.command == "e2e-iteration":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_scenario_e2e.py", "tests/test_architecture.py", "tests/test_contracts.py"]))
    if args.command == "setup":
        checks = [
            [sys.executable, "scripts/check_version_consistency.py"],
            [sys.executable, "scripts/validate_requirement_ledger.py"],
            [sys.executable, "scripts/validate_contract_profile.py"],
            [sys.executable, "scripts/validate_conformance_ledger.py"],
            [sys.executable, "scripts/validate_adrs.py"],
            [sys.executable, "scripts/check_architecture_boundaries.py"],
        ]
        for check in checks:
            result = run(check)
            if result:
                raise SystemExit(result)
        # The Judge commands execute the installed console/package entry point.
        # Install the current checkout into the interpreter running this script
        # so a clean clone needs no PYTHONPATH workaround.
        install = run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "--editable", "."])
        if install:
            raise SystemExit(install)
        print("offline development setup: PASS")
        raise SystemExit(0)
    if args.command == "verify":
        checks = [
            [sys.executable, "scripts/check_format.py"],
            [sys.executable, "scripts/check_markdown_links.py"],
            [sys.executable, "scripts/validate_ci_workflows.py"],
            [sys.executable, "scripts/check_version_consistency.py"],
            [sys.executable, "scripts/check_lock_metadata.py"],
            [sys.executable, "scripts/check_contract_sync.py"],
            [sys.executable, "scripts/validate_requirement_ledger.py"],
            [sys.executable, "scripts/validate_adrs.py"],
            [sys.executable, "scripts/validate_delivery_registry.py"],
            [sys.executable, "scripts/validate_capability_status.py"],
            [sys.executable, "scripts/validate_command_catalog.py"],
            [sys.executable, "scripts/validate_contract_profile.py"],
            [sys.executable, "scripts/validate_conformance_ledger.py"],
            [sys.executable, "scripts/validate_traceability.py"],
            [sys.executable, "scripts/validate_scope_freeze.py"],
            [sys.executable, "scripts/validate_deferred_risk_registers.py"],
            [sys.executable, "scripts/generate_g0_gate_status.py"],
            [sys.executable, "scripts/validate_g0_gate_status.py"],
            [sys.executable, "scripts/generate_claim_registry.py"],
            [sys.executable, "scripts/validate_claim_registry.py"],
            [sys.executable, "scripts/validate_evidence_registry.py"],
            [sys.executable, "scripts/check_architecture_boundaries.py"],
            [sys.executable, "scripts/repository_hygiene.py", "--check"],
        ]
        for check in checks:
            result = run(check)
            if result:
                raise SystemExit(result)
        print("offline repository verification: PASS")
        raise SystemExit(0)
    if args.command == "doctor":
        raise SystemExit(run([sys.executable, "-m", "sentinel_edge.cli", "doctor"]))
    if args.command in {"demo", "scenario"}:
        fixture = "fixtures/scenarios/simultaneous-event.json"
        raise SystemExit(run([sys.executable, "-m", "sentinel_edge.cli", "run-scenario", fixture, "--state-dir", fresh_state(".tmp/dev-scenario-state")]))
    if args.command == "benchmark":
        raise SystemExit(run([sys.executable, "-m", "sentinel_edge.cli", "benchmark", "fixtures/scenarios/benchmark-open-loop.json"]))
    if args.command == "benchmark-replay":
        raise SystemExit(run([sys.executable, "-m", "sentinel_edge.cli", "benchmark-replay", "fixtures/scenarios/benchmark-open-loop.json"]))
    if args.command == "aer":
        raise SystemExit(run([sys.executable, "-m", "sentinel_edge.cli", "after-event-review", "fixtures/scenarios/simultaneous-event.json", "--state-dir", fresh_state(".tmp/dev-aer-state"), "--output", ".tmp/after-event-review.json"]))
    if args.command == "claims":
        claims = run([sys.executable, "scripts/generate_claim_registry.py"])
        if claims:
            raise SystemExit(claims)
        claims = run([sys.executable, "scripts/validate_claim_registry.py"])
        if claims:
            raise SystemExit(claims)
        generate = run([sys.executable, "scripts/generate_release_minimum_manifest.py"])
        if generate:
            raise SystemExit(generate)
        conformance = run([sys.executable, "scripts/generate_conformance_ledger.py"])
        if conformance:
            raise SystemExit(conformance)
        raise SystemExit(run([sys.executable, "scripts/validate_requirement_closure.py"]))
    if args.command == "format":
        raise SystemExit(run([sys.executable, "scripts/check_format.py"]))
    if args.command == "lint":
        raise SystemExit(run([sys.executable, "scripts/check_format.py"]))
    if args.command == "type":
        raise SystemExit(run([sys.executable, "scripts/check_python_types.py"]))
    if args.command == "architecture":
        raise SystemExit(run([sys.executable, "scripts/check_architecture_boundaries.py"]))
    if args.command == "governance":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/governance"]))
    if args.command == "contracts":
        raise SystemExit(run([sys.executable, "scripts/check_contract_sync.py"]))
    if args.command == "no-silent-skips":
        report = ".tmp/pytest-junit.xml"
        pytest_result = run([sys.executable, "-m", "pytest", "-q", "--junitxml", report])
        skip_result = run([sys.executable, "scripts/check_no_silent_skips.py", report]) if Path(report).is_file() else 1
        raise SystemExit(pytest_result or skip_result)
    if args.command == "hygiene":
        raise SystemExit(run([sys.executable, "scripts/repository_hygiene.py", "--check"]))
    if args.command == "gates":
        checks = [
            [sys.executable, "scripts/validate_ci_workflows.py"],
            [sys.executable, "scripts/check_version_consistency.py"],
            [sys.executable, "scripts/check_lock_metadata.py"],
            [sys.executable, "scripts/check_contract_sync.py"],
            [sys.executable, "scripts/validate_capability_status.py"],
            [sys.executable, "scripts/validate_delivery_registry.py"],
            [sys.executable, "scripts/validate_command_catalog.py"],
            [sys.executable, "scripts/validate_contract_profile.py"],
            [sys.executable, "scripts/validate_conformance_ledger.py"],
            [sys.executable, "scripts/validate_traceability.py"],
            [sys.executable, "scripts/validate_scope_freeze.py"],
            [sys.executable, "scripts/validate_deferred_risk_registers.py"],
            [sys.executable, "scripts/generate_g0_gate_status.py"],
            [sys.executable, "scripts/validate_g0_gate_status.py"],
            [sys.executable, "scripts/validate_evidence_registry.py"],
            [sys.executable, "scripts/validate_requirement_closure.py"],
            [sys.executable, "scripts/generate_release_minimum_manifest.py"],
            [sys.executable, "scripts/generate_conformance_ledger.py"],
            [sys.executable, "scripts/validate_claim_registry.py"],
            [sys.executable, "scripts/repository_hygiene.py", "--check"],
            [sys.executable, "-m", "pytest", "-q", "tests/test_release_candidate.py", "tests/test_release_closure_v017.py"],
        ]
        for check in checks:
            result = run(check)
            if result:
                raise SystemExit(result)
        print("G0 release gates: PASS")
        raise SystemExit(0)
    raise SystemExit(run([sys.executable, "-m", "pytest", "-q"]))

if __name__ == "__main__":
    main()
