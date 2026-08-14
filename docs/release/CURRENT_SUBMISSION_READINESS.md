# Current submission readiness

> Generated from repository evidence. Do not hand-edit status claims.

## Candidate

- Candidate ID: `4a9d8b3df501ced147f8ae18e840e1c07bc2f6bcf3b090fad8c41713049581d1`
- Commit: `32845cc0220d9623e48cf58b505132731ca34086`
- Release profile: `H0-EMULATED-AARCH64-20260813`
- Release admitted: `false`

## Arm64 execution environment

- Canonical path: Docker/QEMU `linux/arm64`.
- Intended guest architecture: `aarch64`.
- Physical hardware required for this hackathon profile: **no**.
- Physical sensors required for this hackathon profile: **no**.
- Sensor inputs: deterministic simulated camera, IMU, flood and landslide streams through normal observation contracts.
- Raspberry Pi 5 remains a reference deployment target; emulator results are not Raspberry Pi 5 performance measurements.

## H0 closure

- H0 closed: **240/240**.
- Generated release-minimum status: `True`.

## G0 gate packs

| Gate | Status |
|---|---|
| `G0-01` | `pass` |
| `G0-02` | `pass` |
| `G0-03` | `pass` |
| `G0-04` | `pass` |
| `G0-05` | `pass` |
| `G0-06` | `pass` |
| `G0-07` | `pass` |
| `G0-08` | `pass` |
| `G0-09` | `pass` |
| `G0-10` | `pass` |
| `G0-11` | `pass` |
| `G0-12` | `pass` |

## Judge and Arm64 command matrix

| Command | Status | Exit |
|---|---|---:|
| `setup` | `pass` | `0` |
| `doctor` | `pass` | `0` |
| `verify` | `pass` | `0` |
| `demo` | `pass` | `0` |
| `scenario` | `pass` | `0` |
| `test-all` | `pass` | `0` |
| `gates` | `pass` | `0` |
| `benchmark-replay` | `pass` | `0` |
| `claims` | `pass` | `0` |
| `arm64-setup` | `pass` | `0` |
| `arm64-doctor` | `pass` | `0` |
| `arm64-test` | `pass` | `0` |
| `arm64-demo` | `pass` | `0` |
| `arm64-scenario` | `pass` | `0` |
| `arm64-benchmark` | `pass` | `0` |

## B0/B1/O1 and claims

- Final Arm64-emulated benchmark present: **yes**.
- Benchmark quality guardrails passed: **yes**.
- Benchmark claim class: `simulated`.
- Claim Registry valid source class: `simulated_emulated_arm64`.
- Public Raspberry Pi performance claim allowed: **no**.

## UI / Judge Proof

The Mission Control client exposes all four hazards together, monitoring coverage separately from hazard state, scheduler active/queued/sleeping/deferred state, collaboration status, the emulated-Arm64 disclosure, candidate/release profile information and the persistent research-MVP warning.

## Explicit limitations

- No physical Raspberry Pi validation is claimed.
- No physical camera or IMU validation is claimed.
- No physical energy, thermal or throttling measurement is claimed.
- No field calibration or safety certification is claimed.
- Collaborative email transport is experimental and unverified as peer identity; it is not trusted multi-node confirmation.

## Exact blockers

- `privacy_closure_not_release_eligible`
- `provenance_not_verified`
- `reproducibility_not_verified`

## Remaining manual submission actions (after technical blockers clear)

1. Publish/finalize the public repository and verify the license is visible.
2. Record/edit/upload the final sub-three-minute video from the frozen candidate.
3. Insert the final repository/video URLs into Devpost.
4. Perform the final human Devpost submission.
