# Emulated Arm64 hackathon release profile

The hackathon candidate targets 64-bit Arm Linux and uses one reproducible Docker/QEMU path:

```text
image: python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a
platform: linux/arm64
guest: aarch64 Linux userland
dependency lock: docker/requirements-arm64.lock.txt
publisher artifact manifest: config/arm64-python-artifacts.json
ONNX Runtime: 1.28.0 CPU Execution Provider
runtime proof: real InferenceSession + deterministic known-answer + installed distribution/native-library hashes
sensor mode: deterministic simulated ObservationV2 inputs
```

This profile replaces the physical-device prerequisite for the hackathon candidate. It does not claim Raspberry Pi 5 performance, energy, thermal, or physical-sensor quality. Raspberry Pi 5 remains the reference deployment target.

All simulated camera, IMU, hydrology, and landslide inputs must enter through Component 1 contracts. Component 4 remains the only incident-state writer. Emulation is evidence for Arm64 software execution, reproducibility, architecture, and comparative workload behavior; it is not physical-device evidence.

The profile is intentionally explicit so a truthful limitation is not mistaken for a hardware pass.

## Runtime reproducibility controls

The Docker base is pinned by OCI manifest digest, not only by a mutable tag. The Arm64 dependency lock is a deterministic projection of the hash-pinned Judge/test environment plus exact AArch64 inference-runtime wheels. `config/arm64-python-artifacts.json` binds the publisher-index filenames and SHA-256 values for `flatbuffers`, `numpy`, `protobuf`, and `onnxruntime`; packaging metadata is also locked. The Docker build uses `pip --require-hashes --only-binary=:all:` so a later resolver cannot silently substitute source builds or different wheels. Final `arm64-doctor` and `arm64-benchmark` evidence must contain a passing real ONNX Runtime known-answer inference, CPU-only provider assignment, the installed distribution `RECORD` hash, and native runtime-library hashes.

## Benchmark evidence classes

The deterministic B0/B1/O1 semantic schedule, service times, thermal state, power-quality state and resource-pressure values are simulated policy inputs. The Arm64 guest runner separately records wall time, process CPU time, RSS, real ONNX Runtime known-answer execution and a scheduler-control-plane CPU-overhead microbenchmark as emulator-execution observations. None of those execution observations are Raspberry Pi 5 hardware measurements.
