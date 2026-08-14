# Hackathon H0 profile amendment: emulated Arm64

This amendment is authoritative for the hackathon candidate and is applied to the v0.22 H0 interpretation:

- the execution target is 64-bit Arm Linux in the declared Docker/QEMU `linux/arm64` environment;
- `FR-PLT-001` is accepted from reproducible AArch64 guest evidence with host identity reported separately;
- `FR-PLT-003` is accepted from deterministic simulated camera or IMU input entering the normal Component 1 observation/fixture path;
- physical Raspberry Pi, camera, IMU, and environmental sensors are not required for this candidate;
- physical-device performance, energy, thermal, calibration, and physical-sensor quality claims remain prohibited;
- exactly six components, four hazard adapters, Component 1 acquisition ownership, and Component 4 incident authority are unchanged.

This amendment changes the release profile, not the evidence class: emulation and simulation are explicitly labelled and never presented as physical hardware evidence.
