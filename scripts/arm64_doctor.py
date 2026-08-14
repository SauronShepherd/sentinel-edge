from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main() -> int:
    try:
        import onnxruntime as ort
        ort_version = ort.__version__
        providers = list(ort.get_available_providers())
    except Exception as exc:  # pragma: no cover - guest dependency diagnostic
        ort_version = None
        providers = []
        ort_error = f"{type(exc).__name__}: {exc}"
    else:
        ort_error = None

    model_paths = sorted((ROOT / "artifacts/release-models").rglob("*.onnx"))
    candidate_path = ROOT / "release-candidate.json"
    candidate_id = None
    if candidate_path.is_file():
        try:
            candidate_id = json.loads(candidate_path.read_text(encoding="utf-8")).get("candidate_id")
        except (OSError, json.JSONDecodeError):
            candidate_id = None

    payload = {
        "schema": "sentinel-edge.arm64-doctor.v1",
        "release_profile": "H0-EMULATED-AARCH64-20260813",
        "guest_architecture": platform.machine(),
        "host_architecture": os.environ.get("SENTINEL_HOST_ARCH"),
        "execution_mode": "docker-qemu-linux-arm64",
        "emulated_or_virtualized": True,
        "os": platform.system(),
        "kernel": platform.release(),
        "python": sys.version.split()[0],
        "onnxruntime": {"version": ort_version, "providers": providers, "error": ort_error},
        "candidate_id": candidate_id,
        "benchmark_mode": "emulated_arm64",
        "physical_sensors": False,
        "sensor_input_mode": "deterministic_simulated_or_fixture",
        "raspberry_pi_performance_claim_allowed": False,
        "digests": {
            "emulation_profile": digest(ROOT / "config/arm64-emulation.yaml"),
            "requirements_registry": digest(ROOT / "registries/requirements.yaml"),
            "simultaneous_scenario": digest(ROOT / "fixtures/scenarios/simultaneous-event.json"),
            "benchmark_manifest": digest(ROOT / "fixtures/scenarios/benchmark-open-loop.json"),
            "models": {path.relative_to(ROOT).as_posix(): digest(path) for path in model_paths},
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    valid = payload["guest_architecture"].lower() in {"aarch64", "arm64"} and "CPUExecutionProvider" in providers
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
