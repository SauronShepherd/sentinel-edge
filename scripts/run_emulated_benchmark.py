from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import time
from pathlib import Path

from sentinel_edge.benchmark import DeterministicBenchmarkLab, load_benchmark_manifest
from sentinel_edge.domain.models import BenchmarkVariant
from sentinel_edge.security import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="fixtures/scenarios/benchmark-open-loop.json")
    parser.add_argument("--output", default="qualification/emulated-arm64-benchmark.json")
    args = parser.parse_args()
    manifest_path = ROOT / args.manifest
    output_path = ROOT / args.output
    machine = platform.machine().lower()
    if machine not in {"aarch64", "arm64"}:
        print(json.dumps({"valid": False, "reason": "arm64_guest_required", "observed": machine}, sort_keys=True))
        return 2

    try:
        import onnxruntime as ort
        ort_identity = {"version": ort.__version__, "providers": list(ort.get_available_providers())}
    except Exception as exc:  # pragma: no cover - guest diagnostic
        print(json.dumps({"valid": False, "reason": "onnxruntime_unavailable", "error": str(exc)}, sort_keys=True))
        return 2
    if "CPUExecutionProvider" not in ort_identity["providers"]:
        print(json.dumps({"valid": False, "reason": "cpu_execution_provider_missing", "providers": ort_identity["providers"]}, sort_keys=True))
        return 2

    manifest = load_benchmark_manifest(manifest_path)
    lab = DeterministicBenchmarkLab()
    policy = manifest["benchmark_policy"]
    repeats = int(policy["repeats"])
    warmups = int(policy["warmup_runs"])
    results = {}
    schedule_digests = set()
    for variant in BenchmarkVariant:
        for _ in range(warmups):
            lab.run(manifest, variant)
        wall_samples = []
        cpu_samples = []
        semantic_run = None
        for _ in range(repeats):
            wall_start = time.perf_counter_ns()
            cpu_start = time.process_time_ns()
            semantic_run = lab.run(manifest, variant)
            cpu_samples.append((time.process_time_ns() - cpu_start) / 1_000_000)
            wall_samples.append((time.perf_counter_ns() - wall_start) / 1_000_000)
        assert semantic_run is not None
        schedule_digests.add(semantic_run.schedule_digest)
        results[variant.value] = {
            "semantic": semantic_run.model_dump(mode="json"),
            "emulator_execution": {
                "wall_ms": wall_samples,
                "wall_median_ms": statistics.median(wall_samples),
                "cpu_ms": cpu_samples,
                "cpu_median_ms": statistics.median(cpu_samples),
                "max_rss_kb": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            },
        }

    b0 = results["B0"]["semantic"]
    b1 = results["B1"]["semantic"]
    o1 = results["O1"]["semantic"]
    earthquake_o1 = o1["hazard_quality"].get("earthquake", {})
    quality_checks = {
        "same_opportunity_schedule": len(schedule_digests) == 1,
        "all_variants_offer_same_count": len({b0["offered"], b1["offered"], o1["offered"]}) == 1,
        "all_opportunities_processed": all(row["processed"] == row["offered"] for row in (b0, b1, o1)),
        "model_runtime_optimization_not_worse_than_baseline": b1["median_end_to_end_ms"] <= b0["median_end_to_end_ms"],
        "orchestrator_not_worse_than_b1": o1["median_end_to_end_ms"] <= b1["median_end_to_end_ms"],
        "orchestrator_deadline_misses_not_worse_than_b1": o1["deadline_misses"] <= b1["deadline_misses"],
        "tier_a_earthquake_deadline_preserved_in_o1": earthquake_o1.get("deadline_misses") == 0,
    }
    quality_guardrails_passed = all(quality_checks.values())
    payload = {
        "schema": "sentinel-edge.emulated-arm64-benchmark.v1",
        "release_profile": "H0-EMULATED-AARCH64-20260813",
        "claim_class": "simulated",
        "environment": {
            "guest_architecture": platform.machine(),
            "host_architecture": os.environ.get("SENTINEL_HOST_ARCH"),
            "execution_mode": "docker-qemu-linux-arm64",
            "python": platform.python_version(),
            "onnxruntime": ort_identity,
        },
        "manifest": {"path": args.manifest, "sha256": sha256_file(manifest_path)},
        "quality_checks": quality_checks,
        "quality_guardrails_passed": quality_guardrails_passed,
        "results": results,
        "comparisons": {
            "B0_to_B1_median_end_to_end_ms_delta": b1["median_end_to_end_ms"] - b0["median_end_to_end_ms"],
            "B1_to_O1_median_end_to_end_ms_delta": o1["median_end_to_end_ms"] - b1["median_end_to_end_ms"],
            "B0_to_O1_median_end_to_end_ms_delta": o1["median_end_to_end_ms"] - b0["median_end_to_end_ms"],
            "B0_to_B1_deadline_miss_delta": b1["deadline_misses"] - b0["deadline_misses"],
            "B1_to_O1_deadline_miss_delta": o1["deadline_misses"] - b1["deadline_misses"],
        },
        "limitations": [
            "All hazard opportunities and semantic service times are deterministic simulations.",
            "Wall/CPU/RSS values describe the Arm64-emulated guest process, not Raspberry Pi 5 performance.",
            "No physical energy, thermal, throttling, or sensor-quality claim is made.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if quality_guardrails_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
