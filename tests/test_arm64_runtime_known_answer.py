from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from sentinel_edge.qualification import arm64_runtime


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class _Io:
    name: str


class _Array:
    def __init__(self, value: float) -> None:
        self._value = value

    def reshape(self, _shape: int) -> list[float]:
        return [self._value]

    def __getitem__(self, index: int) -> float:
        return self._value if index == 0 else IndexError(index)


class _Numpy:
    float32 = object()

    @staticmethod
    def asarray(value: object, dtype: object | None = None) -> _Array:
        if isinstance(value, _Array):
            return value
        if isinstance(value, (list, tuple)):
            value = value[0]
        if isinstance(value, (list, tuple)):
            value = value[0]
        return _Array(float(value))

    @staticmethod
    def isfinite(value: float) -> bool:
        return value == value and abs(value) != float("inf")


np = _Numpy()


class _Session:
    def __init__(self, _model: str, *, providers: list[str], output: float = 0.5, assigned: list[str] | None = None) -> None:
        self._providers = assigned or providers
        self._output = output

    def get_providers(self) -> list[str]:
        return list(self._providers)

    def get_inputs(self) -> list[_Io]:
        return [_Io("features")]

    def get_outputs(self) -> list[_Io]:
        return [_Io("score")]

    def run(self, output_names: list[str], feeds: dict[str, object]) -> list[_Array]:
        assert output_names == ["score"]
        assert "features" in feeds
        return [np.asarray([[self._output]], dtype=np.float32)]


def _runtime_identity() -> dict[str, object]:
    return {
        "available": True,
        "distribution": "onnxruntime",
        "version": "1.28.0",
        "record_sha256": "a" * 64,
        "wheel_metadata_sha256": "b" * 64,
        "native_files": {"onnxruntime/capi/onnxruntime_pybind11_state.so": "c" * 64},
    }


def test_real_session_contract_records_cpu_provider_and_known_answer(monkeypatch) -> None:
    fake_ort = SimpleNamespace(
        __version__="1.28.0",
        get_available_providers=lambda: ["CPUExecutionProvider"],
        InferenceSession=lambda model, providers: _Session(model, providers=providers),
    )
    monkeypatch.setattr(arm64_runtime, "onnxruntime_distribution_identity", _runtime_identity)
    result = arm64_runtime.run_onnxruntime_known_answer(ROOT, ort_module=fake_ort, numpy_module=np)
    assert result["passed"] is True
    assert result["assigned_providers"] == ["CPUExecutionProvider"]
    assert result["observed_output"] == 0.5
    assert result["model_bytes"] == (ROOT / "artifacts/release-models/seismic-onnx-development/model.onnx").stat().st_size
    assert result["runtime_distribution"]["record_sha256"] == "a" * 64


def test_known_answer_rejects_provider_fallback(monkeypatch) -> None:
    fake_ort = SimpleNamespace(
        __version__="1.28.0",
        get_available_providers=lambda: ["CPUExecutionProvider", "OtherExecutionProvider"],
        InferenceSession=lambda model, providers: _Session(
            model,
            providers=providers,
            assigned=["CPUExecutionProvider", "OtherExecutionProvider"],
        ),
    )
    monkeypatch.setattr(arm64_runtime, "onnxruntime_distribution_identity", _runtime_identity)
    result = arm64_runtime.run_onnxruntime_known_answer(ROOT, ort_module=fake_ort, numpy_module=np)
    assert result["passed"] is False
    assert "unexpected_provider_assignment_or_fallback" in result["failures"]


def test_known_answer_rejects_wrong_output(monkeypatch) -> None:
    fake_ort = SimpleNamespace(
        __version__="1.28.0",
        get_available_providers=lambda: ["CPUExecutionProvider"],
        InferenceSession=lambda model, providers: _Session(model, providers=providers, output=0.6),
    )
    monkeypatch.setattr(arm64_runtime, "onnxruntime_distribution_identity", _runtime_identity)
    result = arm64_runtime.run_onnxruntime_known_answer(ROOT, ort_module=fake_ort, numpy_module=np)
    assert result["passed"] is False
    assert "known_answer_mismatch" in result["failures"]
