# Sentinel Edge

Sentinel Edge is a local-first Physical AI decision-support system for wildfire, earthquake, flood, and landslide monitoring on constrained Arm edge hardware.

The hackathon candidate was validated in a reproducible emulated/virtualized Arm64 environment. Physical Raspberry Pi and sensor hardware are not required for the judge path: deterministic camera, IMU, rainfall, water-level, soil-moisture, tilt, vibration, clock, thermal, power, storage, and simultaneous-event fixtures exercise the normal acquisition and incident paths.

## What is demonstrated

- Six-component local architecture with deterministic acquisition, analysis, runtime scheduling, incident truth, evidence, and API/UI paths.
- B0/B1/O1 benchmark replay with queue/latency, quality, workload-duty-cycle, memory, and fallback evidence; no physical energy claim is made.
- Explicit abstention and degraded-state behavior when sensors, storage, time, or rich media are unavailable.
- Optional collaborative detection, disabled by default and never required by H0. It shares only derived, privacy-coarsened signals after separate consent; email transport remains experimental and unverified.

## Setup and judge path

From the repository root, run `python scripts/dev.py setup`, `python scripts/dev.py doctor`, `python scripts/dev.py verify`, `python scripts/dev.py demo`, `python scripts/dev.py scenario`, `python scripts/dev.py benchmark-replay`, and `python scripts/dev.py gates`. The documented Arm64 path is `arm64-setup`, `arm64-doctor`, `arm64-test`, `arm64-demo`, `arm64-scenario`, and `arm64-benchmark`.

## Claims and limitations

Claims are evidence-derived and distinguish simulated/fixture evidence from target-qualified physical evidence. No physical-device performance claim is made. The product is not an official warning service and does not perform unsupported disaster prediction or automatic online retraining.

## License and source

The submission repository must expose its Apache-2.0 license and contain the source, fixtures, scripts, and instructions required for offline judging.
