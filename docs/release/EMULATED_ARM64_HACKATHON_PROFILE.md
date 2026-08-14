# Emulated Arm64 hackathon release profile

The hackathon candidate targets 64-bit Arm Linux and uses one reproducible Docker/QEMU path:

```text
image: python:3.13-slim
platform: linux/arm64
guest: aarch64 Linux userland
sensor mode: deterministic simulated ObservationV2 inputs
```

This profile replaces the physical-device prerequisite for the hackathon candidate. It does not claim Raspberry Pi 5 performance, energy, thermal, or physical-sensor quality. Raspberry Pi 5 remains the reference deployment target.

All simulated camera, IMU, hydrology, and landslide inputs must enter through Component 1 contracts. Component 4 remains the only incident-state writer. Emulation is evidence for Arm64 software execution, reproducibility, architecture, and comparative workload behavior; it is not physical-device evidence.

The profile is intentionally explicit so a truthful limitation is not mistaken for a hardware pass.
