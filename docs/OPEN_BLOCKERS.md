# Open blockers — active hackathon profile

**Active profile:** `H0-EMULATED-AARCH64-20260813`
**Scope:** local/offline Judge path plus Docker/QEMU AArch64 execution; no physical Raspberry Pi or physical sensor evidence is required or claimed.

## Submission blocker

1. **Exact final Arm64 emulator rerun and candidate freeze.** Candidate-affecting source/UI/API changes made after the last recorded Arm64 guest receipt require the canonical Docker/QEMU `linux/arm64` command matrix to be rerun on the final Git revision. The current execution sandbox does not provide Docker/QEMU, so this receipt cannot truthfully be regenerated here. Until that rerun is green, `release_admitted` must remain `false` and the final command matrix remains the only technical submission blocker.

## Human/external actions after the green freeze

- Publish the final repository and verify Apache-2.0 is detected/visible.
- Capture screenshots and the sub-three-minute video from the frozen candidate.
- Upload the video, insert final public URLs in Devpost, and submit.

## Explicitly not hackathon blockers

The following belong to the reference Raspberry Pi / H1 / F1 / post-submission lifecycle and must not be allowed to block this H0 emulator candidate: physical camera/IMU qualification, Raspberry Pi power/thermal measurements, field commissioning, site-specific calibration, production secure-boot/key operations, production live-source credentials, production Gmail peer identity, and field-lab deployment hardening. They remain valid contract backlog items, but this candidate makes no claim that they are delivered.
