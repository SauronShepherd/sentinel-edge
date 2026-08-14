from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_arm64_emulation_profile_pins_python_onnxruntime_and_dependency_projection() -> None:
    profile = yaml.safe_load((ROOT / "config/arm64-emulation.yaml").read_text(encoding="utf-8"))
    execution = profile["execution"]
    assert execution["image"] == "python:3.13.15-slim"
    assert execution["image_digest"] == "sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a"
    assert execution["platform"] == "linux/arm64"
    assert execution["guest_architecture"] == "aarch64"
    assert execution["onnxruntime_version"] == "1.28.0"
    assert execution["dependency_lock"] == "docker/requirements-arm64.lock.txt"
    assert execution["network_required_for_judge_path"] is False
    assert execution["network_mode"] == "none"
    assert execution["network_isolation"] == "docker_network_namespace"

    dockerfile = (ROOT / "docker/Dockerfile.arm64").read_text(encoding="utf-8")
    assert "--require-hashes --only-binary=:all:" in dockerfile
    assert "SENTINEL_SETUP_REQUIRE_LOCKED=1 python scripts/bootstrap_local_environment.py" in dockerfile
    assert "pip install --no-cache-dir --no-deps --no-build-isolation --editable ." not in dockerfile
    lock = (ROOT / "docker/requirements-arm64.lock.txt").read_text(encoding="utf-8")
    assert dockerfile.startswith("FROM python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a\n")
    assert "-r /tmp/requirements-arm64.lock.txt" in dockerfile
    for pin in ("flatbuffers==25.2.10", "numpy==2.3.5", "packaging==25.0", "protobuf==6.33.6", "onnxruntime==1.28.0"):
        assert pin in lock
    assert "--hash=sha256:f649dd6f6452d12a8059888aa489fe519e062e18793dac72b9efa0f9fdb64135" in lock
    assert "--hash=sha256:9c75442b2209b8470d6d5d8b1c25714270686f14c749028d2199c54e29f20b4d" in lock
    assert "--hash=sha256:e2afbae9b8e1825e3529f88d514754e094278bb95eadc0e199751cdd9a2e82a2" in lock
    assert "--hash=sha256:ebba5f4d5ea615af3f7fd70fc310636fbb2bbd1f566ac0a23d98dd412de50051" in lock


def test_arm64_doctor_and_benchmark_bind_container_image_identity() -> None:
    doctor = (ROOT / "scripts/arm64_doctor.py").read_text(encoding="utf-8")
    benchmark = (ROOT / "scripts/run_emulated_benchmark.py").read_text(encoding="utf-8")
    runner = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    for source in (doctor, benchmark):
        assert "SENTINEL_ARM64_IMAGE_REF" in source
        assert "SENTINEL_ARM64_IMAGE_ID" in source
        assert "run_onnxruntime_known_answer" in source
    assert '"docker", "image", "inspect"' in runner
    assert "arm64_build_fingerprint" in runner
    assert "org.sentinel-edge.arm64-build-fingerprint" in runner
    assert "content-addressed Arm64 image" in runner
    assert "arm64_dependency_lock" in doctor
    assert "arm64_dockerfile" in doctor
    assert "SENTINEL_ARM64_NETWORK_MODE=none" in runner
    assert '"--network", "none"' in runner


def test_arm64_network_isolation_inspects_kernel_namespace_state(tmp_path, monkeypatch) -> None:
    from sentinel_edge.qualification.arm64_network import inspect_container_network

    net = tmp_path / "net"
    net.mkdir()
    (net / "lo").mkdir()
    route = tmp_path / "route"
    route.write_text("Iface\tDestination\n", encoding="utf-8")
    monkeypatch.setenv("SENTINEL_ARM64_NETWORK_MODE", "none")
    report = inspect_container_network(sys_class_net=net, proc_route=route)
    assert report["valid"] is True
    assert report["below_application_layer_proven"] is True
    assert report["reason_codes"] == ["docker_network_none_namespace_verified"]

    (net / "eth0").mkdir()
    report = inspect_container_network(sys_class_net=net, proc_route=route)
    assert report["valid"] is False
    assert "non_loopback_interface_present" in report["reason_codes"]
