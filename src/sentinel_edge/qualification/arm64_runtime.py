from __future__ import annotations

import hashlib
from importlib import metadata
from pathlib import Path
from typing import Any


EXPECTED_ORT_VERSION = "1.28.0"
EXPECTED_PROVIDER = "CPUExecutionProvider"
DEFAULT_KNOWN_ANSWER_MODEL = "artifacts/release-models/seismic-onnx-development/model.onnx"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def onnxruntime_distribution_identity(*, distribution_name: str = "onnxruntime") -> dict[str, Any]:
    """Return a reproducible fingerprint of the installed ONNX Runtime distribution.

    The wheel's installed RECORD is retained by pip and contains the wheel's file
    inventory and hashes. Binding that file plus native-library hashes is stronger
    evidence than reporting only a version string while avoiding unstable .pyc data.
    """
    try:
        dist = metadata.distribution(distribution_name)
    except metadata.PackageNotFoundError:
        return {
            "available": False,
            "distribution": distribution_name,
            "version": None,
            "record_sha256": None,
            "wheel_metadata_sha256": None,
            "native_files": {},
        }

    files = list(dist.files or ())
    record_path: Path | None = None
    wheel_path: Path | None = None
    native_files: dict[str, str] = {}
    for entry in files:
        rel = str(entry).replace("\\", "/")
        located = Path(dist.locate_file(entry))
        if rel.endswith(".dist-info/RECORD") and located.is_file():
            record_path = located
        elif rel.endswith(".dist-info/WHEEL") and located.is_file():
            wheel_path = located
        elif located.is_file() and (rel.endswith(".so") or ".so." in rel):
            native_files[rel] = _sha256(located)

    return {
        "available": True,
        "distribution": distribution_name,
        "version": dist.version,
        "record_sha256": _sha256(record_path) if record_path else None,
        "wheel_metadata_sha256": _sha256(wheel_path) if wheel_path else None,
        "native_files": dict(sorted(native_files.items())),
    }


def run_onnxruntime_known_answer(
    root: str | Path,
    *,
    ort_module: Any | None = None,
    numpy_module: Any | None = None,
    model_relpath: str = DEFAULT_KNOWN_ANSWER_MODEL,
) -> dict[str, Any]:
    """Execute the admitted tiny ONNX graph through the CPU EP and verify 0.5.

    The released seismic development graph is a MatMul with zero weights followed
    by Sigmoid, so every finite 3-feature input has the deterministic answer 0.5.
    This check intentionally creates a real InferenceSession and records the
    provider assignment, rather than treating importability as runtime proof.
    """
    root_path = Path(root).resolve()
    model_path = (root_path / model_relpath).resolve()
    failures: list[str] = []
    if root_path not in model_path.parents or not model_path.is_file():
        return {
            "schema": "sentinel-edge.arm64-onnxruntime-known-answer.v1",
            "passed": False,
            "model": model_relpath,
            "model_sha256": None,
            "model_bytes": None,
            "requested_providers": [EXPECTED_PROVIDER],
            "assigned_providers": [],
            "expected_output": 0.5,
            "observed_output": None,
            "runtime_distribution": onnxruntime_distribution_identity(),
            "failures": ["known_answer_model_missing_or_outside_root"],
        }

    try:
        if ort_module is None:
            import onnxruntime as ort_module  # type: ignore[no-redef]
        if numpy_module is None:
            import numpy as numpy_module  # type: ignore[no-redef]
    except Exception as exc:  # pragma: no cover - exercised in the Arm guest
        return {
            "schema": "sentinel-edge.arm64-onnxruntime-known-answer.v1",
            "passed": False,
            "model": model_relpath,
            "model_sha256": _sha256(model_path),
            "model_bytes": model_path.stat().st_size,
            "requested_providers": [EXPECTED_PROVIDER],
            "assigned_providers": [],
            "expected_output": 0.5,
            "observed_output": None,
            "runtime_distribution": onnxruntime_distribution_identity(),
            "failures": [f"runtime_dependency_import_failed:{type(exc).__name__}"],
        }

    version = str(getattr(ort_module, "__version__", ""))
    if version != EXPECTED_ORT_VERSION:
        failures.append("onnxruntime_version_mismatch")
    available = list(ort_module.get_available_providers())
    if EXPECTED_PROVIDER not in available:
        failures.append("cpu_execution_provider_unavailable")

    observed: float | None = None
    assigned: list[str] = []
    input_name: str | None = None
    output_name: str | None = None
    try:
        session = ort_module.InferenceSession(str(model_path), providers=[EXPECTED_PROVIDER])
        assigned = list(session.get_providers())
        if assigned != [EXPECTED_PROVIDER]:
            failures.append("unexpected_provider_assignment_or_fallback")
        inputs = list(session.get_inputs())
        outputs = list(session.get_outputs())
        if len(inputs) != 1 or len(outputs) != 1:
            failures.append("known_answer_io_contract_mismatch")
        else:
            input_name = str(inputs[0].name)
            output_name = str(outputs[0].name)
            array = numpy_module.asarray([[1.0, -2.0, 3.0]], dtype=numpy_module.float32)
            raw = session.run([output_name], {input_name: array})
            observed = float(numpy_module.asarray(raw[0]).reshape(-1)[0])
            if not bool(numpy_module.isfinite(observed)):
                failures.append("known_answer_output_non_finite")
            elif abs(observed - 0.5) > 1e-6:
                failures.append("known_answer_mismatch")
    except Exception as exc:  # pragma: no cover - failure diagnostic for Arm guest
        failures.append(f"known_answer_inference_failed:{type(exc).__name__}")

    runtime_identity = onnxruntime_distribution_identity()
    if runtime_identity.get("version") != EXPECTED_ORT_VERSION:
        failures.append("runtime_distribution_version_mismatch")
    if not runtime_identity.get("record_sha256"):
        failures.append("runtime_distribution_record_unbound")
    if not runtime_identity.get("native_files"):
        failures.append("runtime_native_binary_identity_missing")

    return {
        "schema": "sentinel-edge.arm64-onnxruntime-known-answer.v1",
        "passed": not failures,
        "model": model_relpath,
        "model_sha256": _sha256(model_path),
        "model_bytes": model_path.stat().st_size,
        "input_name": input_name,
        "output_name": output_name,
        "requested_providers": [EXPECTED_PROVIDER],
        "available_providers": available,
        "assigned_providers": assigned,
        "expected_output": 0.5,
        "observed_output": observed,
        "runtime_distribution": runtime_identity,
        "failures": sorted(set(failures)),
    }
