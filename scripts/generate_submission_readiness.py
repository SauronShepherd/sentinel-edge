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
    commit, git_state = git_info()
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

    lines = [
        "# Current submission readiness",
        "",
        "> Generated from repository evidence. Do not hand-edit status claims.",
        "",
        "## Candidate",
        "",
        f"- Candidate ID: `{candidate_id}`",
        f"- Commit: `{commit}`",
        f"- Release profile: `{release_profile}`",
        f"- Release admitted: `{str(release_admitted).lower()}`",
        "",
        "## Arm64 execution environment",
        "",
        "- Canonical path: Docker/QEMU `linux/arm64`.",
        "- Intended guest architecture: `aarch64`.",
        "- Physical hardware required for this hackathon profile: **no**.",
        "- Physical sensors required for this hackathon profile: **no**.",
        "- Sensor inputs: deterministic simulated camera, IMU, flood and landslide streams through normal observation contracts.",
        "- Raspberry Pi 5 remains a reference deployment target; emulator results are not Raspberry Pi 5 performance measurements.",
        "",
        "## H0 closure",
        "",
        f"- H0 closed: **{h0_closed}/{h0_total}**.",
        f"- Generated release-minimum status: `{minimum.get('release_admitted', False)}`.",
        "",
        "## G0 gate packs",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for idx in range(1, 13):
        gate = f"G0-{idx:02d}"
        lines.append(f"| `{gate}` | `{packs.get(gate, 'missing')}` |")

    lines += ["", "## Judge and Arm64 command matrix", "", "| Command | Status | Exit |", "|---|---|---:|"]
    required = [
        "setup", "doctor", "verify", "demo", "scenario", "test-all", "gates", "benchmark-replay", "claims",
        "arm64-setup", "arm64-doctor", "arm64-test", "arm64-demo", "arm64-scenario", "arm64-benchmark",
    ]
    for name in required:
        record = commands.get(name, {}) if isinstance(commands.get(name), dict) else {}
        lines.append(f"| `{name}` | `{record.get('status', 'not_run')}` | `{record.get('exit_code', '-')}` |")

    lines += [
        "",
        "## B0/B1/O1 and claims",
        "",
        f"- Final Arm64-emulated benchmark present: **{yn(bool(benchmark))}**.",
        f"- Benchmark quality guardrails passed: **{yn(benchmark.get('quality_guardrails_passed'))}**.",
        f"- Benchmark claim class: `{benchmark.get('claim_class', 'not_bound')}`.",
        f"- Claim Registry valid source class: `{claims.get('claim_ceiling', {}).get('source_class', 'unknown')}`.",
        f"- Public Raspberry Pi performance claim allowed: **{yn(claims.get('claim_ceiling', {}).get('raspberry_pi_performance_claim_allowed'))}**.",
        "",
        "## UI / Judge Proof",
        "",
        "The Mission Control client exposes all four hazards together, monitoring coverage separately from hazard state, scheduler active/queued/sleeping/deferred state, collaboration status, the emulated-Arm64 disclosure, candidate/release profile information and the persistent research-MVP warning.",
        "",
        "## Explicit limitations",
        "",
        "- No physical Raspberry Pi validation is claimed.",
        "- No physical camera or IMU validation is claimed.",
        "- No physical energy, thermal or throttling measurement is claimed.",
        "- No field calibration or safety certification is claimed.",
        "- Collaborative email transport is experimental and unverified as peer identity; it is not trusted multi-node confirmation.",
        "",
        "## Exact blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- None recorded by candidate closure.")
    lines += [
        "",
        "## Remaining manual submission actions (after technical blockers clear)",
        "",
        "1. Publish/finalize the public repository and verify the license is visible.",
        "2. Record/edit/upload the final sub-three-minute video from the frozen candidate.",
        "3. Insert the final repository/video URLs into Devpost.",
        "4. Perform the final human Devpost submission.",
        "",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(OUTPUT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
