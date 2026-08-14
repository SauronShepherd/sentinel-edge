# Sentinel Edge hackathon release notes

## H0 emulated Arm64 candidate

The hackathon release profile is `H0-EMULATED-AARCH64-20260813`. It targets 64-bit Arm Linux and uses one reproducible Docker/QEMU `linux/arm64` path for Arm64 execution evidence. Deterministic simulated camera, IMU, rainfall, water-level, soil-moisture, tilt, vibration, fault, thermal-pressure, power-pressure, and storage-pressure inputs enter through the normal acquisition contracts.

### Included H0 behavior

- Exactly four hazard adapters: wildfire, earthquake, flood, and landslide.
- Exactly six top-level components, with Component 4 as the sole incident-lifecycle mutation authority.
- Criticality/deadline orchestration with a reserved earthquake path, bounded queues, maximum deferral, forced wildfire scans, overload visibility, and static fallback.
- Deterministic simultaneous-event scenario and recovery path.
- Local evidence/provenance, review, REST integration boundary, and Mission Control client.
- B0/B1/O1 benchmark architecture with Arm64-emulated execution evidence required before final candidate admission.
- Candidate-bound Claim Registry and fail-closed release admission.
- Optional Collaborative Detection extension, disabled by default, with offline fixture transport and experimental Gmail-shaped polling/validation lane.

### Release closure changes

- Physical-device-only blockers were removed from the hackathon H0 profile without weakening hardware-specific claim restrictions.
- Release candidate admission now requires the canonical Judge/Arm64 command matrix and a valid AArch64-emulated B0/B1/O1 artifact.
- Generated candidate files no longer invalidate an otherwise clean source revision merely by being generated.
- Source-bound SBOM, security, privacy, reproducibility, and provenance evidence can be regenerated with `scripts/prepare_release_evidence.py`.
- Mission Control visibly discloses the emulated environment and deterministic sensor simulation.

The final `release_admitted` flag remains false until the exact Git revision is clean and the full Arm64 command matrix is green.
