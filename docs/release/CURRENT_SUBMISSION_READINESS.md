# Current submission readiness

> Generated from repository evidence. Do not hand-edit status claims.

## 1. Candidate ID and commit

- Candidate ID: `6edc40d19d492d1d89f0b31104813b38f4a7c2184907d1af53c73fc012636b31`
- Commit: `45a6e4b03d38a464f479db9a4a8e6c9ee9ef8559`
- Release admitted: `true`

## 2. Exact H0 release profile

- Release profile: `H0-EMULATED-AARCH64-20260813`
- Track intent: Physical AI hackathon candidate.
- Exactly six top-level product components remain in force.
- Exactly four hazard adapters remain in force: wildfire, earthquake, flood, landslide.
- Component 1 remains the acquisition boundary; Component 4 remains the sole incident-lifecycle authority.

## 3. Arm64 execution environment

- Canonical guest architecture: `aarch64`.
- Recorded host architecture for bundled benchmark evidence: `AMD64`.
- Python: `3.13.15`.
- ONNX Runtime: `1.28.0`.
- Execution providers: `AzureExecutionProvider, CPUExecutionProvider`.
- Canonical guest image pin: `python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a`.
- Arm64 dependency lock: `docker/requirements-arm64.lock.txt` (`sha256:65e0ef9403f0185d2703ad45f0dc7bb4190d7b66151d1fe8b40a92097a280b25`).
- Arm64 publisher-artifact manifest: `config/arm64-python-artifacts.json` (`sha256:2cbde396290997f4c09b8317155dcfff690bda8888bed9fee16ac1aef06eafea`); the Docker build uses `pip --require-hashes --only-binary=:all:`.
- Resolved benchmark container image ID: `not_bound_in_prior_benchmark`.
- ONNX Runtime known-answer inference: **no**; assigned providers: `not_bound`.
- Installed ONNX Runtime RECORD fingerprint: `not_bound`; native runtime files bound: **0**.
- Physical hardware required for this hackathon profile: **no**.
- Physical sensors required for this hackathon profile: **no**.

## 4. Emulation / virtualization technology

- Canonical path: `docker-qemu-linux-arm64`.
- The documented local path uses Docker/OCI `linux/arm64` with QEMU/binfmt-backed Arm64 execution where native Arm64 is unavailable.
- Canonical guest runs use Docker `--network none`; final Arm64 doctor/benchmark evidence must verify a loopback-only guest namespace with no default route.
- Raspberry Pi 5 remains the reference deployment target; emulator results are not Raspberry Pi 5 performance measurements.

## 5. Sensor simulation strategy

- Wildfire: deterministic frame/video fixtures with normal, smoke-like and ambiguous-negative sequences, timestamps, persistence and evidence-clip behavior.
- Earthquake: deterministic fixed-rate three-axis IMU fixtures with background vibration, earthquake-like waveform, hard negatives, clock metadata and Tier-A scheduling.
- Flood: deterministic rainfall, water-level, rate-of-rise, threshold, stale/missing and recovery states.
- Landslide: deterministic rainfall accumulation, soil moisture where applicable, tilt/vibration, missingness and movement-anomaly states.
- All simulated inputs enter through the normal Component-1 observation/source contracts; scenario code does not inject incident state directly.

## 6. G0-01 through G0-12 status

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

## 7. H0 closure status

- H0 closed: **240/240**.
- Generated release-minimum admission field: `True`.
- Gate evidence is classified under the declared emulated profile; no physical-device evidence is fabricated.
- Latest local simultaneous-event proof: `not loaded`.
- Scenario transcript digest: `not_loaded`.
- Scenario invariant-report digest: `not_loaded`.

## 8. Judge command status

The post-change local and Arm64 command matrix is bound in `qualification/submission-command-matrix.json`; each required lane below passed.

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

## 9. B0 / B1 / O1 status

- Bundled Arm64-emulated benchmark present: **yes**.
- Benchmark quality guardrails passed: **yes**.
- Benchmark claim class: `simulated`.
- Current benchmark evidence schema includes final scheduler/workload instrumentation: **no**.
- Arm64 scheduler-overhead measurement class: `not_bound_until_final_arm64_rerun`.

| Variant | Median semantic E2E | p95 semantic E2E | Deadline misses |
|---|---:|---:|---:|
| B0 | 111.5 ms | 137.0 ms | 3 |
| B1 | 80.5 ms | 97.0 ms | 1 |
| O1 | 69.0 ms | 97.0 ms | 0 |

These are deterministic semantic workload results from retained Arm64-emulated evidence. The final revision requires a fresh `arm64-benchmark` because the benchmark schema now also binds queue/service totals, heavy-workload duty/invocation counts, explicit simulated resource labels and measured-emulator scheduler overhead. They are not Raspberry Pi 5 latency measurements.

## 10. Claim Registry status

- Claim Registry source class ceiling: `simulated_emulated_arm64`.
- Public Raspberry Pi performance claim allowed: **no**.
- Public optimization wording is restricted to truthful comparative Arm64-emulated workload behavior and architecture effects.

## 11. UI / Judge Proof status

- Machine-readable UIX conformance: **23/23 passed** (`pass`).
- UIX H0 checks: **22/22 passed**.
- UIX design basis bound: **10 reference mockups + specification digest**; reference mockups remain design inputs, not runtime evidence.
- The responsive local client implements the supplied UIX workspace language and the ten reference screen patterns.
- Mission Control exposes all four hazards together, system health and coverage separately, scheduler running/queued/sleeping/deferred state, decision reasons, evidence, uncertainty, review actions and source/input mode.
- Benchmark Lab exposes B0/B1/O1 evidence and limitations; Judge Proof exposes candidate/profile and G0/H0 proof data.
- The application persistently discloses the Arm64-emulated/simulated-input environment and the Research MVP safety boundary.
- Collaborative Detection is visibly experimental, opt-in and default-off; simulated peers are not presented as authenticated real peers.

## 12. Public package status

- Root license target: Apache-2.0 as declared in submission materials.
- Judge guide, Devpost copy, video script/shot list/overlays, screenshot plan, third-party notices and release limitations are present in the repository.
- Final public repository publication, public video URL and Devpost form submission remain human/external actions.
- Final `dist/judge-package/` and exact release-candidate manifest must be regenerated only after the complete post-change preflight succeeds.

## 13. Explicit limitations

- No physical Raspberry Pi validation is claimed.
- No physical camera or IMU validation is claimed.
- No physical energy, thermal or throttling measurement is claimed.
- No field calibration or safety certification is claimed.
- Collaborative email transport is experimental and unverified as peer identity; it is not trusted multi-node confirmation.
- The required Docker/QEMU-backed Arm64 guest rerun is bound and green in the command matrix; no physical Raspberry Pi or sensor pass is implied.

## 14. Remaining manual submission actions

1. On a local machine with Docker/QEMU Arm64 support, run the exact final `submission-preflight` / Arm64 command matrix after this revision and freeze a new candidate if all lanes are green.
2. Publish/finalize the public repository and verify the license is visible.
3. Capture product screenshots and record/edit/upload the final sub-three-minute video from that frozen candidate.
4. Insert the final repository/video URLs into Devpost and perform the final human submission.

## 15. Exact blockers, if any

- None recorded by candidate closure.

A truthful declared limitation is acceptable; a fabricated hardware pass is not.
