# Sentinel Edge

**Research MVP — not an official emergency-warning service.**

Sentinel Edge is an **offline-first, Arm64-targeted Physical AI platform** for running four heterogeneous hazard-monitoring workloads on one constrained edge node. Its central contribution is a criticality- and deadline-aware workload orchestrator that protects the earthquake path, wakes and sleeps heavier wildfire processing, adapts lower-priority work, and keeps degradation visible under contention and faults.

> **Research MVP — not an official emergency-warning system. AI observations and forecasts may be wrong. Verify with authorized sources and contact emergency services when appropriate.**

## Hackathon release profile

The current hackathon profile is **`H0-EMULATED-AARCH64-20260813`**.

- Execution target: 64-bit Arm Linux / AArch64.
- Canonical evidence environment: Docker + QEMU `linux/arm64`.
- Sensor input: deterministic simulated/fixture camera, IMU and environmental streams through the normal acquisition contract.
- Physical Raspberry Pi: not required for this candidate.
- Physical camera/IMU/environmental sensors: not required for this candidate.
- Raspberry Pi 5 remains the reference deployment target, **not** the device on which the hackathon benchmark numbers are physically measured.
- No physical Pi energy, thermal, throttling, sensor-quality or latency claim is made without physical evidence.

The package implementation version remains `0.21.0`; the active product and technical contracts are `0.22.0`. Those are intentionally separate version axes and are checked by `scripts/check_version_consistency.py`.

## Why this is Physical AI

Sentinel Edge consumes physical-world signal shapes—camera frames, three-axis IMU, rainfall, water level, soil moisture, tilt and vibration—and makes local observation/escalation decisions. In the hackathon candidate those signal streams are deterministic simulations, but they enter through the same Component-1 observation boundary intended for physical adapters. Scenario fixtures never write incident state directly.

## Four hazard adapters

| Hazard | H0 depth | Demonstration |
|---|---|---|
| Wildfire | Hero | Camera smoke cascade/equivalent, temporal persistence, wake/sleep heavy processing, evidence clip |
| Earthquake | Hero | Fixed-rate IMU, deterministic trigger, Tier-A reserved dispatch, waveform evidence |
| Flood | Bounded functional | Rainfall/water-level validation, rate of rise, thresholds, missing/stale handling |
| Landslide | Bounded functional | Rainfall, soil/tilt/vibration movement indicators, missingness, context-adaptive cadence |

## Exactly six top-level components

1. **Streaming Source Collector** — acquisition, quarantine and normalized observations.
2. **Analysis & Enrichment Engine** — deterministic/qualified analysis outputs, not incident authority.
3. **Model & Workload Runtime** — qualified workload execution and the scheduler.
4. **Incident & Event Engine** — the **sole incident-lifecycle mutation authority**.
5. **REST API & Integration Gateway** — supported client/integration command and query boundary.
6. **Client Applications** — responsive Mission Control/PWA projections and commands through Component 5.

Module-owned persistence and explicit ports are used instead of direct cross-component table coupling.

## Optimization story: B0 → B1 → O1

Sentinel Edge keeps one deterministic opportunity manifest and compares:

- **B0** — naive fixed-rate reference behavior.
- **B1** — optimized model/runtime/preprocessing behavior at fixed rate.
- **O1** — the same optimized profiles plus criticality/deadline orchestration and adaptive cadence.

```text
B0 → B1 = model/runtime/preprocessing effect
B1 → O1 = scheduling/adaptive-cadence effect
B0 → O1 = total platform effect
```

The emulated benchmark reports deterministic semantic scheduling results plus Arm64-emulated guest wall/CPU/RSS observations. Its current schema also records queue/service totals, heavy-workload invocation/duty-cycle accounting, and a scheduler-control-plane CPU-overhead microbenchmark measured inside the AArch64 guest. Thermal, power and pressure values in the semantic scenario remain explicitly simulated policy inputs. These are **not Raspberry Pi 5 measurements**.

## Fastest Judge path

From a clean checkout/source archive:

```bash
python scripts/dev.py setup
python scripts/dev.py doctor
python scripts/dev.py demo
```

`setup` is offline-friendly: it installs a standard site-packages `.pth` for the checkout (no `PYTHONPATH` environment hack) and either verifies the exact hash-pinned `requirements-dev.lock.txt` or, for ordinary local Judge/demo use only, reuses an already-installed environment that satisfies the declared project ranges. It records the mode in `.tmp/setup-environment.json`. Final `submission-preflight` disables that compatibility fallback and requires the exact hash-pinned dependency set.

To open the seeded UIX-aligned local Mission Control workspace:

```bash
python scripts/dev.py ui
# http://127.0.0.1:8000/client
# local read-only token: sentinel-dev-viewer-token

# Machine-readable conformance against the supplied UIX specification
# and all ten reference-screen families:
python scripts/dev.py uix
```

`ui` resets and runs the deterministic simultaneous-event fixture before serving the application on loopback, so the screens contain real Component-4 incident projections produced through the normal scenario path rather than direct UI-only state injection.

Deeper local proof:

```bash
python scripts/dev.py verify
python scripts/dev.py scenario
python scripts/dev.py test-all
python scripts/dev.py gates
python scripts/dev.py benchmark-replay
python scripts/dev.py claims
```

The H0 Judge path requires no live source, cloud account, API key, second board, physical sensor or private credential.

## Canonical Arm64-emulated path

Docker must support `linux/arm64` through its normal emulation/virtualization mechanism.

```bash
python scripts/dev.py arm64-setup
python scripts/dev.py arm64-doctor
python scripts/dev.py arm64-test
python scripts/dev.py arm64-demo
python scripts/dev.py arm64-scenario
python scripts/dev.py arm64-benchmark
```

`arm64-doctor` reports guest and host architecture separately, exact Python/ONNX Runtime identity, execution providers, selected profile and key model/config/fixture digests. It must report an AArch64 guest and `CPUExecutionProvider`. The base image is immutably pinned to `python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a`; the generated Arm64 lock pins the full Judge/test environment and exact AArch64 inference-runtime artifacts. `config/arm64-python-artifacts.json` binds publisher-index wheel filenames and SHA-256 values for NumPy, Protobuf, FlatBuffers and ONNX Runtime, while the Docker build enforces `pip --require-hashes --only-binary=:all:`. Guest evidence records the resolved Docker image ID. Doctor and benchmark instantiate the admitted ONNX model through `CPUExecutionProvider`, execute a deterministic known-answer inference, and bind the installed ONNX Runtime `RECORD` plus native-library hashes. Every canonical guest run uses Docker `--network none`; doctor/benchmark evidence verifies the guest namespace exposes loopback only and has no default route before Arm64 benchmark evidence is accepted.

`arm64-benchmark` writes `qualification/emulated-arm64-benchmark.json`. The artifact explicitly separates deterministic simulated workload/resource semantics from emulator-execution observations, binds real AArch64 ONNX Runtime execution, records heavy-workload and queue/service accounting, and measures scheduler Python control-plane overhead inside the guest. It refuses hardware-specific claims.

## Final release closure

The repository has a two-stage release workflow so generated evidence cannot accidentally self-invalidate the candidate.

First run the complete preflight:

```bash
python scripts/dev.py submission-preflight
```

This records the required local and Arm64 command matrix at:

```text
qualification/submission-command-matrix.json
```

Commit the resulting deterministic evidence/generator changes, verify the worktree is clean, then create the exact candidate:

```bash
python scripts/dev.py release-candidate
```

Release admission fails closed when any of these is true:

- the repository has no real Git revision or has source/config/evidence changes;
- the submission command matrix is absent, stale or not fully green;
- any H0 requirement remains open;
- any G0 pack fails;
- the Claim Registry is invalid;
- required release/supply-chain evidence does not verify;
- the emulated profile is inconsistent with its no-physical-hardware/no-Pi-performance claim policy.

Generated `release-candidate.json`, `release-manifest.json` and candidate signature files are excluded from the Git cleanliness calculation because they are outputs of candidate creation itself. Other changes still invalidate the candidate.

## Deterministic simultaneous-event scenario

```bash
python scripts/dev.py scenario
```

The scenario exercises normal multi-hazard monitoring, smoke/rain/water/slope/IMU changes, scheduler contention, Tier-A seismic reservation, wildfire wake/sleep, adaptive flood/landslide cadence, lower-priority deferral, bounded queues, fail-visible overload, source/sensor failure, deterministic worker crash/recovery, clock/storage pressure and recovery through normal component boundaries. Replayed/backfill evidence is never promoted into fresh evidence. The generated proof also reads the resulting four-hazard projection through the supported local Component-5 REST boundary; it does not inject UI or incident state directly.

## Mission Control

The H0 client is implemented as a dependency-free responsive PWA aligned to `docs/design/UIX_SPECIFICATION.md` and the generated reference mockups. It reproduces the persistent top bar/sidebar, object-centric navigation, split views, inspectors, filters, tables, KPI cards, status pills, report/benchmark views and mobile drawer behavior while using Sentinel Edge hazard semantics rather than the cybersecurity placeholder data in the design references.

The implemented surfaces include Overview, Sites, Devices, Sensors, Cameras, Incidents, AI Investigation, Alerts, Dashboards, Reports, Policies, Automation, Firmware & Updates, Deploy New Site, Integrations, Collaborative Detection, Benchmark Lab, Judge Proof and Administration. The investigation assistant is evidence-linked support only; it has no critical-state authority.

The Judge-facing UI shows:

- all four hazards together;
- system health separately from hazard state;
- monitoring coverage separately from hazard state;
- running/queued/sleeping/deferred jobs and reason codes;
- evidence/timeline and review state;
- fixture/simulated/replayed source labels;
- candidate identity;
- benchmark view;
- the persistent research-MVP warning;
- the explicit Arm64-emulated demonstration disclosure;
- B0/B1/O1 absolute benchmark values from the bundled emulated evidence;
- all twelve G0 gate packs through a read-only Judge Proof endpoint;
- optional Collaborative Detection consent and transport-trust boundaries, default OFF.

## Collaborative Detection (optional H1/S8)

Collaborative Detection is **disabled by default** and is never an H0 dependency. It can share small privacy-minimized event-level signals, not raw sensor/media streams. Operational sharing consent and future research contribution consent are separate.

Offline checks:

```bash
python scripts/dev.py collaboration-check
python scripts/dev.py collaboration-demo
python scripts/dev.py collaboration-gmail-fixture
python scripts/dev.py test-collaboration
```

Email transport is experimental and must never be presented as cryptographically authenticated peer verification. Local monitoring continues unchanged when collaboration is disabled or unavailable. The implementation includes hazard-aware privacy transformation, material-event signal generation, bounded outbound SMTP retry/suppression, durable Gmail receipt idempotency, Component-4 independent-peer correlation, a module-owned SQLite persistence option, deterministic JSON/`.eml` fixtures, low-cardinality metrics, and UI/API trust disclosures.

## Important directories

```text
architecture/       executable architecture/command/policy truth
config/             release and optional feature configuration
contracts/          generated/shared contract packages
fixtures/           deterministic Judge/scenario/benchmark inputs
modules/            six top-level component packages
provenance/         evidence and submission-media metadata
qualification/      generated qualification, G0, claim and release truth
registries/         requirements, ADRs, tasks, tests and evidence registries
schemas/            released JSON schemas
scripts/dev.py      canonical developer/Judge command surface
src/sentinel_edge/  compact Python implementation
```

## Contracts and conformance

The active contracts are:

- `docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md`
- `docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md`

They define 743 product requirements, including the 240-row H0 cutline, and 193 binding ADRs. The hackathon emulation amendment is implemented as the selected release profile rather than by fabricating physical-device qualification.

Useful checks:

```bash
python scripts/check_contract_sync.py
python scripts/validate_delivery_registry.py
python scripts/validate_requirement_ledger.py
python scripts/validate_requirement_closure.py
python scripts/generate_release_minimum_manifest.py
python scripts/generate_g0_gate_status.py
python scripts/validate_g0_gate_status.py
```

## Safety and claim boundaries

Sentinel Edge does **not** claim:

- earthquake prediction;
- official emergency warnings or dispatch authority;
- safety certification;
- exact wildfire ignition coordinates from one monocular camera;
- guaranteed flooding from one uncertain forecast;
- imminent landslide timing from an unvalidated model;
- a universal combined disaster probability;
- Raspberry Pi 5 performance from emulated execution;
- physical energy/thermal/throttling behavior from simulated policy transitions.

Simulation, replay, target and research results remain visibly distinct from physical measurements.

## License

Apache-2.0. See `LICENSE` and the third-party inventory/notices for dependency, model, fixture and data-rights information.

## Additional repository validation lanes

The canonical command catalog also exposes focused maintenance/verification lanes. They are not needed for the three-command Judge demo, but remain available for maintainers and CI:

```text
format  lint  type  architecture  governance  contracts
no-silent-skips  hygiene  test-all  gates
aer  plugins  testkit  components  clients  packages  compatibility  generated
security  privacy  accessibility  provenance  docs  report  package
backup-verify  update-verify  test-arm
```

Invoke any lane as `python scripts/dev.py <command>`.
