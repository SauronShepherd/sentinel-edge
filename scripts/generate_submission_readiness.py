from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/release/CURRENT_SUBMISSION_READINESS.md"


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def git_info() -> tuple[str, str]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        return commit, "available"
    except (OSError, subprocess.CalledProcessError):
        return "unavailable in source archive", "unavailable"


def yn(value: object) -> str:
    return "yes" if value is True else "no"


def main() -> int:
    candidate = load_json(ROOT / "release-candidate.json", {})
    matrix = load_json(ROOT / "qualification/submission-command-matrix.json", {})
    gates = load_json(ROOT / "qualification/g0-gate-status.json", {})
    minimum = load_json(ROOT / "qualification/release-minimum-manifest.json", {})
    claims = load_json(ROOT / "qualification/claim-registry.json", {})
    benchmark = load_json(ROOT / "qualification/emulated-arm64-benchmark.json", {})
    uix = load_json(ROOT / "qualification/uix-conformance.json", {})
    scenario_proof = load_json(ROOT / ".tmp/scenario-proof/proof.json", {})
    _diagnostic_head, git_state = git_info()
    candidate_repo = candidate.get("identity", {}).get("repository_state", {}) if isinstance(candidate.get("identity"), dict) else {}
    commit = candidate_repo.get("revision") or "not yet bound to a final release candidate"
    release_profile = candidate.get("release_profile") or gates.get("release_profile") or "H0-EMULATED-AARCH64-20260813"
    candidate_id = candidate.get("candidate_id") or "not yet generated for final revision"
    release_admitted = bool(candidate.get("release_admitted", False))
    blockers = list(candidate.get("admission_blockers", []))
    # The exact release-candidate builder is the blocker authority.  Only derive
    # blockers here when no candidate has been generated yet.  This avoids
    # reporting aliases for the same missing preflight/benchmark evidence.
    if not candidate:
        if git_state != "available":
            blockers.append("git_revision_unavailable")
        if matrix.get("overall_status") != "pass":
            blockers.append("submission_command_matrix_not_green")
        if not benchmark or benchmark.get("quality_guardrails_passed") is not True:
            blockers.append("final_emulated_arm64_benchmark_not_bound")
    blockers = sorted(set(blockers))

    packs = {item.get("id"): item.get("status") for item in gates.get("packs", []) if isinstance(item, dict)}
    h0_total = int(minimum.get("requirement_count", 240) or 240)
    h0_closed = int(minimum.get("closed_count", 0) or 0)
    commands = matrix.get("commands", {}) if isinstance(matrix.get("commands"), dict) else {}
    required_local = matrix.get("required_local_commands", []) if isinstance(matrix.get("required_local_commands"), list) else []
    required_arm64 = matrix.get("required_arm64_commands", []) if isinstance(matrix.get("required_arm64_commands"), list) else []
    local_preflight_pass = bool(required_local) and all(
        isinstance(commands.get(name), dict) and commands[name].get("status") == "pass" for name in required_local
    )
    arm64_preflight_pass = bool(required_arm64) and all(
        isinstance(commands.get(name), dict) and commands[name].get("status") == "pass" for name in required_arm64
    )
    preflight_pass = matrix.get("overall_status") == "pass" and local_preflight_pass and arm64_preflight_pass

    benchmark_results = benchmark.get("results", {}) if isinstance(benchmark.get("results"), dict) else {}
    b0 = benchmark_results.get("B0", {}).get("semantic", {}) if isinstance(benchmark_results.get("B0"), dict) else {}
    b1 = benchmark_results.get("B1", {}).get("semantic", {}) if isinstance(benchmark_results.get("B1"), dict) else {}
    o1 = benchmark_results.get("O1", {}).get("semantic", {}) if isinstance(benchmark_results.get("O1"), dict) else {}
    environment = benchmark.get("environment", {}) if isinstance(benchmark.get("environment"), dict) else {}
    ort = environment.get("onnxruntime", {}) if isinstance(environment.get("onnxruntime"), dict) else {}
    image = environment.get("container_image", {}) if isinstance(environment.get("container_image"), dict) else {}
    known_answer = environment.get("known_answer_inference", {}) if isinstance(environment.get("known_answer_inference"), dict) else {}
    runtime_distribution = known_answer.get("runtime_distribution", {}) if isinstance(known_answer.get("runtime_distribution"), dict) else {}
    # Keep the canonical guest pin and dependency-lock digest explicit.
    import hashlib
    arm_lock = ROOT / "docker/requirements-arm64.lock.txt"
    arm_lock_sha = hashlib.sha256(arm_lock.read_bytes()).hexdigest() if arm_lock.is_file() else "missing"
    arm_artifacts = ROOT / "config/arm64-python-artifacts.json"
    arm_artifacts_sha = hashlib.sha256(arm_artifacts.read_bytes()).hexdigest() if arm_artifacts.is_file() else "missing"
    benchmark_instrumentation = benchmark.get("instrumentation", {}) if isinstance(benchmark.get("instrumentation"), dict) else {}
    scheduler_overhead = benchmark_instrumentation.get("scheduler_overhead", {}) if isinstance(benchmark_instrumentation.get("scheduler_overhead"), dict) else {}
    benchmark_current_schema = bool(
        scheduler_overhead.get("measurement_class") == "measured_emulated_arm64"
        and all(
            {"total_service_ms", "total_queue_delay_ms", "heavy_model_invocation_count", "heavy_model_duty_cycle", "scheduler_decision_count"} <= set(row)
            for row in (b0, b1, o1)
        )
    )
    if preflight_pass:
        command_status_note = "The post-change local and Arm64 command matrix is bound in `qualification/submission-command-matrix.json`; each required lane below passed."
    else:
        command_status_note = "The exact final candidate command matrix is not yet green. The table below is generated only from `qualification/submission-command-matrix.json`; missing entries remain `not_run`."
    if benchmark_current_schema and arm64_preflight_pass:
        benchmark_note = "These are deterministic semantic workload results from the current Arm64-emulated evidence. They are not Raspberry Pi 5 latency measurements."
    else:
        benchmark_note = "These are deterministic semantic workload results from retained Arm64-emulated evidence. The final revision requires a fresh `arm64-benchmark` because the benchmark schema now also binds queue/service totals, heavy-workload duty/invocation counts, explicit simulated resource labels and measured-emulator scheduler overhead. They are not Raspberry Pi 5 latency measurements."

    lines = [
        "# Current submission readiness",
        "",
        "> Generated from repository evidence. Do not hand-edit status claims.",
        "",
        "## 1. Candidate ID and commit",
        "",
        f"- Candidate ID: `{candidate_id}`",
        f"- Commit: `{commit}`",
        f"- Release admitted: `{str(release_admitted).lower()}`",
        "",
        "## 2. Exact H0 release profile",
        "",
        f"- Release profile: `{release_profile}`",
        "- Track intent: Physical AI hackathon candidate.",
        "- Exactly six top-level product components remain in force.",
        "- Exactly four hazard adapters remain in force: wildfire, earthquake, flood, landslide.",
        "- Component 1 remains the acquisition boundary; Component 4 remains the sole incident-lifecycle authority.",
        "",
        "## 3. Arm64 execution environment",
        "",
        f"- Canonical guest architecture: `{environment.get('guest_architecture', 'aarch64')}`.",
        f"- Recorded host architecture for bundled benchmark evidence: `{environment.get('host_architecture', 'not_bound')}`.",
        f"- Python: `{environment.get('python', 'not_bound')}`.",
        f"- ONNX Runtime: `{ort.get('version', 'not_bound')}`.",
        f"- Execution providers: `{', '.join(ort.get('providers', [])) if isinstance(ort.get('providers'), list) else 'not_bound'}`.",
        "- Canonical guest image pin: `python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a`.",
        f"- Arm64 dependency lock: `docker/requirements-arm64.lock.txt` (`sha256:{arm_lock_sha}`).",
        f"- Arm64 publisher-artifact manifest: `config/arm64-python-artifacts.json` (`sha256:{arm_artifacts_sha}`); the Docker build uses `pip --require-hashes --only-binary=:all:`.",
        f"- Resolved benchmark container image ID: `{image.get('id', 'not_bound_in_prior_benchmark')}`.",
        f"- ONNX Runtime known-answer inference: **{yn(known_answer.get('passed'))}**; assigned providers: `{known_answer.get('assigned_providers', 'not_bound')}`.",
        f"- Installed ONNX Runtime RECORD fingerprint: `{runtime_distribution.get('record_sha256', 'not_bound')}`; native runtime files bound: **{len(runtime_distribution.get('native_files', {})) if isinstance(runtime_distribution.get('native_files'), dict) else 0}**.",
        "- Physical hardware required for this hackathon profile: **no**.",
        "- Physical sensors required for this hackathon profile: **no**.",
        "",
        "## 4. Emulation / virtualization technology",
        "",
        f"- Canonical path: `{environment.get('execution_mode', 'docker-qemu-linux-arm64')}`.",
        "- The documented local path uses Docker/OCI `linux/arm64` with QEMU/binfmt-backed Arm64 execution where native Arm64 is unavailable.",
        "- Canonical guest runs use Docker `--network none`; final Arm64 doctor/benchmark evidence must verify a loopback-only guest namespace with no default route.",
        "- Raspberry Pi 5 remains the reference deployment target; emulator results are not Raspberry Pi 5 performance measurements.",
        "",
        "## 5. Sensor simulation strategy",
        "",
        "- Wildfire: deterministic frame/video fixtures with normal, smoke-like and ambiguous-negative sequences, timestamps, persistence and evidence-clip behavior.",
        "- Earthquake: deterministic fixed-rate three-axis IMU fixtures with background vibration, earthquake-like waveform, hard negatives, clock metadata and Tier-A scheduling.",
        "- Flood: deterministic rainfall, water-level, rate-of-rise, threshold, stale/missing and recovery states.",
        "- Landslide: deterministic rainfall accumulation, soil moisture where applicable, tilt/vibration, missingness and movement-anomaly states.",
        "- All simulated inputs enter through the normal Component-1 observation/source contracts; scenario code does not inject incident state directly.",
        "",
        "## 6. G0-01 through G0-12 status",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for idx in range(1, 13):
        gate = f"G0-{idx:02d}"
        lines.append(f"| `{gate}` | `{packs.get(gate, 'missing')}` |")

    lines += [
        "",
        "## 7. H0 closure status",
        "",
        f"- H0 closed: **{h0_closed}/{h0_total}**.",
        f"- Generated release-minimum admission field: `{minimum.get('release_admitted', False)}`.",
        "- Gate evidence is classified under the declared emulated profile; no physical-device evidence is fabricated.",
        f"- Latest local simultaneous-event proof: **{sum(bool(v) for v in scenario_proof.get('invariants', {}).values())}/{len(scenario_proof.get('invariants', {})) or 0} invariants passed**" if scenario_proof else "- Latest local simultaneous-event proof: `not loaded`.",
        f"- Scenario transcript digest: `{scenario_proof.get('transcript_sha256', 'not_loaded')}`.",
        f"- Scenario invariant-report digest: `{scenario_proof.get('invariant_report_sha256', 'not_loaded')}`.",
        "",
        "## 8. Judge command status",
        "",
        command_status_note,
        "",
        "| Command | Status | Exit |",
        "|---|---|---:|",
    ]
    required = [
        "setup", "doctor", "verify", "demo", "scenario", "test-all", "gates", "benchmark-replay", "claims",
        "arm64-setup", "arm64-doctor", "arm64-test", "arm64-demo", "arm64-scenario", "arm64-benchmark",
    ]
    for name in required:
        record = commands.get(name, {}) if isinstance(commands.get(name), dict) else {}
        lines.append(f"| `{name}` | `{record.get('status', 'not_run')}` | `{record.get('exit_code', '-')}` |")

    lines += [
        "",
        "## 9. B0 / B1 / O1 status",
        "",
        f"- Bundled Arm64-emulated benchmark present: **{yn(bool(benchmark))}**.",
        f"- Benchmark quality guardrails passed: **{yn(benchmark.get('quality_guardrails_passed'))}**.",
        f"- Benchmark claim class: `{benchmark.get('claim_class', 'not_bound')}`.",
        f"- Current benchmark evidence schema includes final scheduler/workload instrumentation: **{yn(benchmark_current_schema)}**.",
        f"- Arm64 scheduler-overhead measurement class: `{scheduler_overhead.get('measurement_class', 'not_bound_until_final_arm64_rerun')}`.",
        "",
        "| Variant | Median semantic E2E | p95 semantic E2E | Deadline misses |",
        "|---|---:|---:|---:|",
        f"| B0 | {b0.get('median_end_to_end_ms', '-')} ms | {b0.get('p95_end_to_end_ms', '-')} ms | {b0.get('deadline_misses', '-')} |",
        f"| B1 | {b1.get('median_end_to_end_ms', '-')} ms | {b1.get('p95_end_to_end_ms', '-')} ms | {b1.get('deadline_misses', '-')} |",
        f"| O1 | {o1.get('median_end_to_end_ms', '-')} ms | {o1.get('p95_end_to_end_ms', '-')} ms | {o1.get('deadline_misses', '-')} |",
        "",
        benchmark_note,
        "",
        "## 10. Claim Registry status",
        "",
        f"- Claim Registry source class ceiling: `{claims.get('claim_ceiling', {}).get('source_class', 'unknown')}`.",
        f"- Public Raspberry Pi performance claim allowed: **{yn(claims.get('claim_ceiling', {}).get('raspberry_pi_performance_claim_allowed'))}**.",
        "- Public optimization wording is restricted to truthful comparative Arm64-emulated workload behavior and architecture effects.",
        "",
        "## 11. UI / Judge Proof status",
        "",
        f"- Machine-readable UIX conformance: **{uix.get('summary', {}).get('passed_count', 0)}/{uix.get('summary', {}).get('requirement_count', 0)} passed** (`{uix.get('summary', {}).get('overall_status', 'not_generated')}`).",
        f"- UIX H0 checks: **{uix.get('summary', {}).get('h0_passed', 0)}/{uix.get('summary', {}).get('h0_count', 0)} passed**.",
        f"- UIX design basis bound: **{uix.get('design_basis', {}).get('reference_mockup_count', 0)} reference mockups + specification digest**; reference mockups remain design inputs, not runtime evidence.",
        "- The responsive local client implements the supplied UIX workspace language and the ten reference screen patterns.",
        "- Mission Control exposes all four hazards together, system health and coverage separately, scheduler running/queued/sleeping/deferred state, decision reasons, evidence, uncertainty, review actions and source/input mode.",
        "- Benchmark Lab exposes B0/B1/O1 evidence and limitations; Judge Proof exposes candidate/profile and G0/H0 proof data.",
        "- The application persistently discloses the Arm64-emulated/simulated-input environment and the Research MVP safety boundary.",
        "- Collaborative Detection is visibly experimental, opt-in and default-off; simulated peers are not presented as authenticated real peers.",
        "",
        "## 12. Public package status",
        "",
        "- Root license target: Apache-2.0 as declared in submission materials.",
        "- Judge guide, Devpost copy, video script/shot list/overlays, screenshot plan, third-party notices and release limitations are present in the repository.",
        "- Final public repository publication, public video URL and Devpost form submission remain human/external actions.",
        "- Final `dist/judge-package/` and exact release-candidate manifest must be regenerated only after the complete post-change preflight succeeds.",
        "",
        "## 13. Explicit limitations",
        "",
        "- No physical Raspberry Pi validation is claimed.",
        "- No physical camera or IMU validation is claimed.",
        "- No physical energy, thermal or throttling measurement is claimed.",
        "- No field calibration or safety certification is claimed.",
        "- Collaborative email transport is experimental and unverified as peer identity; it is not trusted multi-node confirmation.",
        *( [
            "- The required Docker/QEMU-backed Arm64 guest rerun is bound and green in the command matrix; no physical Raspberry Pi or sensor pass is implied.",
        ] if arm64_preflight_pass else [
            "- A required post-change Docker/QEMU-backed Arm64 guest rerun is not yet bound and green; existing Arm64 receipts must not be misrepresented as a post-change rerun.",
        ] ),
        "",
        "## 14. Remaining manual submission actions",
        "",
        "1. On a local machine with Docker/QEMU Arm64 support, run the exact final `submission-preflight` / Arm64 command matrix after this revision and freeze a new candidate if all lanes are green.",
        "2. Publish/finalize the public repository and verify the license is visible.",
        "3. Capture product screenshots and record/edit/upload the final sub-three-minute video from that frozen candidate.",
        "4. Insert the final repository/video URLs into Devpost and perform the final human submission.",
        "",
        "## 15. Exact blockers, if any",
        "",
    ]
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- None recorded by candidate closure.")
    lines += ["", "A truthful declared limitation is acceptable; a fabricated hardware pass is not.", ""]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(OUTPUT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
