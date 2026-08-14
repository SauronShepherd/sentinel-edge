from __future__ import annotations
import argparse
import hashlib
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # clean-checkout setup bootstrap
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
ARM64_IMAGE_PREFIX = "sentinel-edge:arm64-emulated"


def load_command_catalog() -> list[dict[str, object]]:
    catalog_path = ROOT / "architecture/command-catalog.yaml"
    text = catalog_path.read_text(encoding="utf-8")
    if yaml is None:
        # A pristine Python installation may not have PyYAML yet. Recover only
        # the command names with the standard library so `setup` can install the
        # pinned environment without requiring a pre-existing project dependency.
        names = re.findall(r"^\s*-\s+name:\s*([A-Za-z0-9_-]+)\s*$", text, flags=re.MULTILINE)
        if not names:
            raise SystemExit("command_catalog_bootstrap_parse_failed")
        bootstrap_internal = {"test-workstream", "e2e-iteration"}
        return [{"name": name, "internal": name in bootstrap_internal} for name in names]
    payload = yaml.safe_load(text) or {}
    commands = payload.get("commands", [])
    if not isinstance(commands, list):
        raise SystemExit("command_catalog_invalid:commands_not_a_list")
    return commands


def arm64_build_fingerprint() -> str:
    digest = hashlib.sha256()
    for rel in ("docker/Dockerfile.arm64", "docker/requirements-arm64.lock.txt", "config/arm64-emulation.yaml", "pyproject.toml"):
        path = ROOT / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def arm64_image_ref() -> str:
    return f"{ARM64_IMAGE_PREFIX}-{arm64_build_fingerprint()[:16]}"


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
    fingerprint = arm64_build_fingerprint()
    image_ref = arm64_image_ref()
    if build:
        image_present = subprocess.run(
            ["docker", "image", "inspect", image_ref],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if not image_present:
            result = run([
                "docker", "build", "--platform", "linux/arm64",
                "--build-arg", f"SENTINEL_ARM64_BUILD_FINGERPRINT={fingerprint}",
                "-f", "docker/Dockerfile.arm64", "-t", image_ref, ".",
            ])
            if result:
                return result
        else:
            print(f"reusing content-addressed Arm64 image: {image_ref}")
    image_id = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image_ref],
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()
    image_fingerprint = subprocess.run(
        ["docker", "image", "inspect", "--format", '{{ index .Config.Labels "org.sentinel-edge.arm64-build-fingerprint" }}', image_ref],
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()
    if not image_id:
        print(f"arm64 emulation unavailable: image identity missing for {image_ref}")
        return 2
    if image_fingerprint != fingerprint:
        print(f"arm64 emulation rejected: image fingerprint mismatch for {image_ref}")
        return 2
    return run([
        "docker", "run", "--rm", "--platform", "linux/arm64", "--network", "none",
        "-e", f"SENTINEL_HOST_ARCH={platform.machine()}",
        "-e", "SENTINEL_ARM64_NETWORK_MODE=none",
        "-e", f"SENTINEL_ARM64_IMAGE_REF={image_ref}",
        "-e", f"SENTINEL_ARM64_IMAGE_ID={image_id}",
        "-e", f"SENTINEL_ARM64_BUILD_FINGERPRINT={fingerprint}",
        "-v", f"{ROOT}:/workspace", "-w", "/workspace", image_ref, "python", *args,
    ])


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
        # Resume only receipts bound to this exact source tree and setup/runtime
        # fingerprint. A changed checkout or environment automatically clears
        # the partial run rather than inheriting stale acceptance evidence.
        raise SystemExit(run([sys.executable, "scripts/run_test_all.py", "--resume"]))
    if args.command == "arm64-setup":
        raise SystemExit(run_arm64("--help", build=True))
    if args.command == "arm64-doctor":
        raise SystemExit(run_arm64("scripts/arm64_doctor.py", build=False))
    if args.command == "arm64-test":
        raise SystemExit(run_arm64(
            "-m", "pytest", "-q",
            "tests/test_architecture.py",
            "tests/test_arm64_emulation_profile.py",
            "tests/test_arm64_runtime_known_answer.py",
            "tests/test_scheduler.py",
            "tests/test_scenario_e2e.py",
            "tests/test_scenario_faults.py",
            "tests/test_submission_scenario_proof.py",
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
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q",
            "tests/test_collaboration_contracts.py",
            "tests/test_collaboration_config.py",
            "tests/test_collaboration_config_validation.py",
            "tests/test_collaboration_factory.py",
            "tests/test_collaboration_policy.py",
            "tests/test_collaboration_privacy.py",
            "tests/test_collaboration_repository.py",
            "tests/test_collaboration_spec_fixtures.py",
            "tests/test_collaboration_wire.py",
        ]))
    if args.command == "test-collaboration":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_collaboration_api.py", "tests/test_collaboration_config.py", "tests/test_collaboration_config_validation.py", "tests/test_collaboration_contracts.py", "tests/test_collaboration_factory.py", "tests/test_collaboration_fixture.py", "tests/test_collaboration_gmail.py", "tests/test_collaboration_policy.py", "tests/test_collaboration_privacy.py", "tests/test_collaboration_repository.py", "tests/test_collaboration_service.py", "tests/test_collaboration_spec_fixtures.py", "tests/test_collaboration_smtp.py", "tests/test_collaboration_wire.py"]))
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
    if args.command == "human-acceptance":
        raise SystemExit(run([sys.executable, "scripts/human_acceptance.py"]))
    if args.command == "plugins":
        raise SystemExit(run([sys.executable, "scripts/run_capability_lane.py", "plugins"]))
    if args.command == "testkit":
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/contracts"]))
    if args.command == "components":
        raise SystemExit(run([sys.executable, "scripts/run_capability_lane.py", "components"]))
    if args.command == "clients":
        raise SystemExit(run_lane(
            [sys.executable, "scripts/generate_uix_conformance.py"],
            [sys.executable, "scripts/check_client_boundaries.py"],
            [sys.executable, "-m", "pytest", "-q",
             "tests/test_client_security.py",
             "tests/test_client_accessibility.py",
             "tests/test_client_localization_mobile.py",
             "tests/test_mission_control_uix.py",
             "tests/test_uix_reference_screens.py",
             "tests/test_uix_conformance_report.py",
             "tests/test_web_boundary_integration.py",
             "tests/test_web_security_policy.py"],
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
            [sys.executable, "scripts/generate_uix_conformance.py"],
            [sys.executable, "scripts/generate_submission_readiness.py"],
        ))
    if args.command == "package":
        package_command = [sys.executable, "scripts/build_judge_package.py"]
        candidate_path = ROOT / "release-candidate.json"
        if candidate_path.is_file():
            try:
                import json as _json
                candidate_payload = _json.loads(candidate_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                candidate_payload = {}
            if candidate_payload.get("release_admitted") is True:
                # A frozen admitted candidate must prove the public package from
                # a fresh copy. Pre-candidate development packaging stays fast.
                package_command.append("--verify-local")
        raise SystemExit(run_lane(
            [sys.executable, "scripts/repository_hygiene.py", "--check"],
            [sys.executable, "scripts/check_lock_metadata.py"],
            package_command,
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
        # Provision the checkout without PYTHONPATH. A clean environment gets
        # the hash-pinned uv export; an already-compatible offline environment
        # may be reused for ordinary Judge/demo work. Release preflight sets
        # SENTINEL_SETUP_REQUIRE_LOCKED=1 and therefore requires the exact lock.
        bootstrap = run([sys.executable, "scripts/bootstrap_local_environment.py"])
        if bootstrap:
            raise SystemExit(bootstrap)
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
        print("clean-checkout setup: PASS (see .tmp/setup-environment.json for dependency mode)")
        raise SystemExit(0)
    if args.command == "verify":
        checks = [
            [sys.executable, "scripts/check_format.py"],
            [sys.executable, "scripts/check_markdown_links.py"],
            [sys.executable, "scripts/validate_ci_workflows.py"],
            [sys.executable, "scripts/check_version_consistency.py"],
            [sys.executable, "scripts/check_lock_metadata.py"],
            [sys.executable, "scripts/generate_arm64_dependency_lock.py", "--check"],
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
            [sys.executable, "scripts/validate_submission_claim_materials.py"],
            [sys.executable, "scripts/generate_uix_conformance.py"],
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
        fixture = "fixtures/scenarios/simultaneous-event.signed.json"
        public_key = "fixtures/scenarios/simultaneous-event.public.pem"
        raise SystemExit(run([
            sys.executable, "-m", "sentinel_edge.cli", "run-scenario", fixture,
            "--state-dir", fresh_state(".tmp/dev-scenario-state"),
            "--public-key", public_key,
        ]))
    if args.command == "ui":
        raise SystemExit(run([sys.executable, "scripts/serve_demo.py"]))
    if args.command == "uix":
        generate = run([sys.executable, "scripts/generate_uix_conformance.py"])
        if generate:
            raise SystemExit(generate)
        raise SystemExit(run([sys.executable, "-m", "pytest", "-q", "tests/test_uix_conformance_report.py", "tests/test_uix_reference_screens.py", "tests/test_mission_control_uix.py"]))
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
        materials = run([sys.executable, "scripts/validate_submission_claim_materials.py"])
        if materials:
            raise SystemExit(materials)
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
            # Run the mutation-sensitive candidate tests first so release-input
            # validation does not accumulate subprocess/file-system state before
            # they snapshot the repository.  The set is unchanged; only order is.
            [sys.executable, "-m", "pytest", "-q", "tests/test_release_candidate.py", "tests/test_release_closure_v017.py"],
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
            [sys.executable, "scripts/validate_submission_claim_materials.py"],
            [sys.executable, "scripts/generate_uix_conformance.py"],
            [sys.executable, "scripts/repository_hygiene.py", "--check"],
        ]
        for check in checks:
            label = " ".join(str(part) for part in check[1:])
            print(f"gate: {label}", flush=True)
            result = run(check)
            if result:
                raise SystemExit(result)
        print("G0 release gates: PASS")
        raise SystemExit(0)
    raise SystemExit(run([sys.executable, "-m", "pytest", "-q"]))

if __name__ == "__main__":
    main()
