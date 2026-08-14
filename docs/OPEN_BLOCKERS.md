# Open blockers

**Version:** 0.21.0  
**Open H0 requirements:** governed by the emulated-Arm64 release profile; no blocker is retained solely because physical hardware is unavailable.

The physical/target release remains blocked by the items below. Repository-side local/emulation work completed during this pass is called out separately in `docs/release/CURRENT_SUBMISSION_READINESS.md`.

1. Canonical Docker/QEMU AArch64 setup, doctor, test, scenario, and benchmark receipts still need to be captured for this candidate; Docker is unavailable on the current host. This is an emulated execution requirement, not a Raspberry Pi hardware requirement.
2. Publisher-origin Arm64 wheels, exact target lock closure and no-index installation rehearsal on the qualified target image.
3. Deterministic simulated camera/IMU signal-chain receipts through Component 1 need final release-candidate binding. The local scenario path itself is implemented and passing; physical camera/IMU capture is outside this profile.
4. Exact ONNX Runtime session creation and inference on the target, including provider assignment/fallback proof, memory ceilings, hostile-graph corpus and known-answer execution on the released package.
5. Target model-quality evidence bound to the exact released graph, preprocessing, runtime, platform envelope and physical signal chain.
6. Site commissioning on deployed hardware with verified mounting, calibration, datum/baseline, evidence windows and replacement/remount procedures.
7. Simulated power/thermal/storage-pressure policy transitions and final emulation-labelled evidence pack remain to be completed; physical energy is not claimed.
8. B0/B1/O1 replay results now exist locally with truthful `simulated` claim classes; final release binding remains to be completed and Raspberry Pi target measurements are not claimed.
9. Site-specific flood/landslide calibration and field validation.
10. Qualified authenticated time and exact geospatial transformation/datum evidence.
11. Production parser sandboxing with network namespace/seccomp and independent assessment.
12. Complete external-recipient/cache/replica discovery and secure-erasure qualification.
13. A genuinely independent second builder/host and reproducible target binaries, models and images.
14. Current authoritative advisory ingestion, complete inventory/reachability and independently reviewed VEX.
15. Customer-key secure boot or an explicitly accepted restricted-deployment limitation.
16. Independent security, privacy and accessibility reviews and deployed release-credential operations.
17. Closure of remaining repository-side H0 evidence and all release-gate proof packs under the emulated profile.
