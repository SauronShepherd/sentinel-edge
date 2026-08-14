# Sentinel Edge development plan — hackathon freeze first

## 1. Active hackathon profile

The active candidate is `H0-EMULATED-AARCH64-20260813`. It uses the single Docker/QEMU `linux/arm64` profile in `config/arm64-emulation.yaml`. Deterministic camera, three-axis IMU, rainfall, water-level, soil-moisture, tilt and vibration streams enter through normal Component-1 contracts and remain visibly simulated. Emulation can establish Arm64 software execution and comparative workload evidence; it cannot establish Raspberry Pi latency/power/thermal or physical-sensor quality.

Canonical final freeze sequence:

```text
python scripts/dev.py arm64-setup
python scripts/dev.py arm64-doctor
python scripts/dev.py arm64-test
python scripts/dev.py arm64-demo
python scripts/dev.py arm64-scenario
python scripts/dev.py arm64-benchmark
python scripts/dev.py submission-preflight
python scripts/dev.py release-candidate
```

No new feature work is admitted if it threatens an H0 G0 gate.

## 2. Optional H1/S8 Collaborative Detection

Collaborative Detection remains **default OFF** and never becomes an H0 dependency. Its local/offline submission-safe implementation now includes the versioned schemas/types, separate operational/research consent, privacy transformation, material-event signal factory, bounded fixture/email abstractions, Gmail `.eml` fixture path, Component-1 normalization, Component-4 hazard-specific correlation, independent-peer accounting, explicit decision traces, low-cardinality metrics, REST projections, UI settings/trust disclosures and offline tests. Real Gmail remains optional and `email_unverified`; it cannot create trusted real multi-node confirmation.

The submission-safe demo is fixture-qualified simulated peers only. If collaboration causes any H0 gate regression, the rollback remains:

```yaml
collaboration:
  enabled: false
```

## 3. Post-submission / reference Raspberry Pi work

Only after the hackathon candidate is frozen should the project spend time on the reference physical target and field-lab profile:

1. Capture a Raspberry Pi 5 runtime envelope and publisher-origin Arm64 wheelhouse on that exact image.
2. Qualify physical IMU/camera signal chains, mounting, calibration and sensor timing.
3. Measure native Pi latency/RSS plus physical power, thermal and throttling behavior.
4. Renew model-quality evidence against exact physical signal chains and runtime/provider identity.
5. Commission field sites, storage/update/backup controls and site-specific flood/landslide calibration.
6. Complete independent builder/security/privacy/accessibility and broader H1/F1 qualification.

These are not claims of the current hackathon candidate.
