# Target evidence handoff

This document defines the only evidence that may close the two remaining H0
requirements. Fixture, emulator, development-host, bounded ONNX inspection and
commissioning-fixture results must remain non-target evidence.

## REQ-PLT-001 — native 64-bit Arm Linux

Run on the qualified Raspberry Pi 5 target, from the exact release checkout:

```text
python3 -m sentinel_edge.cli doctor > artifacts/target-doctor.json
python3 scripts/dev.py verify
python3 scripts/record_test_evidence.py --help
```

The target receipt must preserve the doctor output, the exact checkout/package
identity, kernel and OS identity, board model, CPU architecture, CPU features,
thermal/PSI/power observations, and SHA-256 bindings for all attached reports.
The receipt is acceptable only when the observed machine is 64-bit Arm Linux;
an x86_64 development result must remain non-target evidence.

## REQ-PLT-003 — locally captured physical signal path

Use a physically connected camera or IMU and the signed signal-chain profile.
Capture the raw input and run the corresponding commissioning command:

```text
python3 -m sentinel_edge.cli commission-imu <raw-capture> --source-id <source> --rate-hz <rate> --output artifacts/imu-commissioning.json
python3 -m sentinel_edge.cli commission-camera <raw-capture> --source-id <source> --fps <fps> --output artifacts/camera-commissioning.json
```

Only the command matching the actually connected sensor may be used. The
receipt must bind the raw capture digest, signal-chain profile digest, device
identity, qualified timestamps, anti-aliasing/saturation checks, calibration
and mounting observations, and the resulting commissioning report. A fixture,
replayed file, Android emulator or remote API cannot satisfy this requirement.

## Promotion rule

Do not change either requirement from `CONFIRMED` until the target receipt is
stored in `provenance/evidence/`, its digest is entered in
`registries/evidence.yaml`, and the requirement receives a matching
`verification_evidence_ids` entry. Run the deterministic closure, conformance,
evidence-registry and legacy delivery framework validators after promotion. Until then, the release
minimum manifest must continue to show both requirements as open.
