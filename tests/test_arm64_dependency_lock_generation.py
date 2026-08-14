from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    path = ROOT / "scripts/generate_arm64_dependency_lock.py"
    spec = importlib.util.spec_from_file_location("generate_arm64_dependency_lock", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_arm64_dependency_lock_is_deterministic_projection() -> None:
    module = _module()
    assert (ROOT / "docker/requirements-arm64.lock.txt").read_text(encoding="utf-8") == module.render()


def test_arm64_artifact_manifest_binds_canonical_aarch64_runtime_wheels() -> None:
    payload = json.loads((ROOT / "config/arm64-python-artifacts.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "sentinel-edge.arm64-python-artifacts.v1"
    by_name = {item["name"]: item for item in payload["artifacts"]}
    assert by_name["onnxruntime"]["filename"].endswith("manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl")
    assert by_name["onnxruntime"]["sha256"] == "f649dd6f6452d12a8059888aa489fe519e062e18793dac72b9efa0f9fdb64135"
    assert by_name["numpy"]["sha256"] == "9c75442b2209b8470d6d5d8b1c25714270686f14c749028d2199c54e29f20b4d"
    assert by_name["protobuf"]["sha256"] == "e2afbae9b8e1825e3529f88d514754e094278bb95eadc0e199751cdd9a2e82a2"
    assert all(item["source_url"].startswith("https://pypi.org/project/") for item in payload["artifacts"])
