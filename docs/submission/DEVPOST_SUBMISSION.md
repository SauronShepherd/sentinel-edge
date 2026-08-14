# Sentinel Edge

## Tagline

**Offline-first multi-hazard Physical AI with criticality-aware Arm orchestration — demonstrated reproducibly on emulated AArch64 with deterministic sensor streams.**

## Project overview

Wildfire cameras, seismic IMUs and environmental sensors have very different urgency, cadence and compute requirements. A naive edge deployment runs each workload independently at a fixed rate and lets the operating system arbitrate contention without knowing that an earthquake trigger has a tighter deadline than a flood-context refresh or a background wildfire scan.

**Sentinel Edge** is an offline-first Physical AI platform for exactly four current hazards — **wildfire, earthquake, flood and landslide** — running on one constrained Arm64 edge target. Its central contribution is an **Arm AI Orchestrator** that schedules validated work using criticality, deadlines, minimum cadence, maximum deferral, current evidence, queue pressure and device health.

The hackathon candidate uses the explicit release profile `H0-EMULATED-AARCH64-20260813`: a reproducible Docker/QEMU `linux/arm64` environment with deterministic simulated camera, three-axis IMU, rainfall, water-level, soil-moisture, tilt and vibration streams. Those inputs enter the same Component-1 observation contract used by physical adapters; the scenario never injects incident state directly. Physical Raspberry Pi or sensor hardware is not required for judging.

Sentinel Edge is a **research MVP**, not an official emergency-warning system or safety-certified instrument. It detects earthquake-like shaking only after shaking begins, does not claim exact wildfire ignition coordinates from one camera, and keeps observation, uncertainty, coverage and official-source authority separate.

## What it does

### Four end-to-end hazard paths

- **Wildfire — hero path:** simulated camera sequence, frame/capture-age handling, smoke-like persistence, ambiguous-negative/abstention behavior, heavy-inference wake/sleep policy and pre/post-trigger evidence clip.
- **Earthquake — hero path:** fixed-rate simulated three-axis IMU stream, deterministic low-cost trigger, waveform retention, visible clock quality and reserved Tier-A scheduler dispatch.
- **Flood — bounded functional path:** rainfall, water level, rate-of-rise, threshold crossing/recovery, typed missing/stale values and deterministic fallback.
- **Landslide — bounded functional path:** rainfall accumulation, soil/tilt/vibration context, movement anomaly, missingness and post-rain/post-seismic cadence adaptation.

### Simultaneous-event scenario

A deterministic scenario drives the ordinary acquisition path and demonstrates smoke, heavy rainfall, rising water, slope-instability signals and an earthquake-like IMU trigger under contention. It exercises bounded queues, workload deferral, Tier-A reservation, source/network failure, sensor missingness, worker recovery, storage/clock/device-pressure policies, replay/backfill freshness guards, evidence creation and Component-4 incident-state transitions.

### Mission Control / Judge Proof

The responsive local PWA follows the provided Sentinel Edge UIX design language: persistent navigation/top bar, KPI cards, tables, filters, object inspectors, split views and responsive mobile behavior. It includes:

- Overview and four-hazard Mission Control;
- separate system health and monitoring coverage;
- running / queued / sleeping / deferred scheduler state and reasons;
- evidence, uncertainty and review actions;
- Sites, Devices, Sensors, Cameras and Incident workspaces;
- evidence-linked AI Investigation support with **no incident-state authority**;
- Policies, Reports, Provisioning, Firmware and Automation UIX surfaces;
- Benchmark Lab with B0/B1/O1 proof;
- Judge Proof with all G0 packs and release identity;
- optional Collaborative Detection consent/trust UI, default OFF;
- persistent `Research MVP` and `Arm64 emulated demonstration` disclosures.

## Architecture

Sentinel Edge has **exactly six top-level components**:

1. Streaming Source Collector — acquisition and normalized observations.
2. Analysis & Enrichment Engine — analysis outputs, never incident authority.
3. Model & Workload Runtime — validated execution and scheduling.
4. Incident & Event Engine — **sole incident-lifecycle mutation authority**.
5. REST API & Integration Gateway — supported client/integration boundary.
6. Client Applications — responsive web/PWA projections and commands through Component 5.

This keeps the simulation honest: fixtures use the same normal boundaries intended for physical adapters instead of scenario-only shortcuts.

## How it was optimized for Arm

Sentinel Edge separates model/runtime optimization from workload orchestration with three comparable variants:

- **B0 — naive fixed-rate baseline.** Learned work uses its baseline profile and workloads run at fixed cadence without shared criticality-aware orchestration.
- **B1 — optimized runtime, fixed-rate.** Validated model/runtime/preprocessing profiles are used at the same offered cadence.
- **O1 — optimized runtime + orchestrator.** The same optimized profiles are combined with criticality/deadline scheduling, earthquake reservation, wildfire wake/sleep behavior, bounded queues and adaptive cadence.

The canonical emulated environment runs **AArch64 Linux** from the immutable `python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a` base. `docker/requirements-arm64.lock.txt` hash-pins the Judge/test environment plus exact AArch64 inference-runtime wheels; `config/arm64-python-artifacts.json` binds publisher-index filenames and SHA-256 values, and Docker installs binary wheels with `--require-hashes --only-binary=:all:`. Doctor/benchmark instantiate the admitted ONNX graph through **CPUExecutionProvider**, execute a deterministic known-answer inference, reject provider fallback, fingerprint the installed runtime distribution/native libraries, and record the resolved Docker image identity. The benchmark runner refuses non-Arm64 guest execution and records host and guest architectures separately.

## Benchmark results

**Claim class: `simulated` / Arm64-emulated comparative evidence. These are not Raspberry Pi 5 measurements.**

The variants use the same deterministic opportunity schedule and quality/instrumentation guardrails:

| Variant | Median semantic end-to-end | p95 | Deadline misses |
|---|---:|---:|---:|
| `B0` | **111.5 ms** | 137 ms | 3 |
| `B1` | **80.5 ms** | 97 ms | 1 |
| `O1` | **69.0 ms** | 97 ms | 0 |

Attribution on this deterministic workload:

- `B0 → B1`: **−31.0 ms** median semantic E2E.
- `B1 → O1`: **−11.5 ms** additional median semantic E2E.
- `B0 → O1`: **−42.5 ms** total median semantic E2E, with deadline misses reduced from **3 to 0**.

Quality checks in the retained bundled evidence confirm the same opportunity schedule/count, complete opportunity processing, non-regression of the optimized runtime/orchestrator comparison and preservation of the Tier-A earthquake deadline in O1. The final benchmark schema also records queue/service totals and heavy-workload invocation/duty-cycle accounting, explicitly labels thermal/power/resource-pressure inputs as simulated, and separately measures scheduler-control-plane CPU overhead inside the AArch64 guest. The final frozen candidate must regenerate that evidence after the last source change.

We deliberately do **not** publish emulated values as Raspberry Pi latency, power, energy, temperature, throttling or production throughput. Raspberry Pi 5 remains the reference deployment target, not the hardware on which these numbers were physically measured.

## Collaborative Detection — optional experimental extension

Collaborative Detection is H1/S8, **disabled by default**, and never an H0 dependency. A node may separately opt into operational sharing and future research contribution. Only small derived event-level signals are permitted after privacy transformation; raw camera/video/audio, raw IMU/environmental streams, exact coordinates, user identity and credentials are excluded.

The initial email/Gmail transport is deliberately classified `email_unverified`: it may support experimental review-level correlation but is not cryptographic peer identity and cannot create trusted real multi-node confirmation. The Judge demo uses fixture-qualified simulated peers and works fully offline. The local implementation includes bounded outbound retry/suppression, durable Gmail receipt idempotency, hazard-specific correlation domains, independent-peer accounting, deterministic JSON/`.eml` negative fixtures, and a Mission Control/incident UI that keeps local evidence, collaborative evidence and transport trust separate.

## How to run it

### Fast no-hardware Judge flow

```bash
python scripts/dev.py setup
python scripts/dev.py doctor
python scripts/dev.py demo
```

The ordinary local setup can reuse an already-installed compatible environment when offline and records that mode; final submission preflight requires the exact hash-pinned dependency lock. The checkout is made importable through a standard site-packages `.pth`, not an undocumented `PYTHONPATH` override.

Open the seeded local product UI:

```bash
python scripts/dev.py ui
# http://127.0.0.1:8000/client
# viewer token: sentinel-dev-viewer-token
```

Deeper proof:

```bash
python scripts/dev.py verify
python scripts/dev.py scenario
python scripts/dev.py test-all
python scripts/dev.py gates
python scripts/dev.py benchmark-replay
python scripts/dev.py claims
```

### Reproduce Arm64 execution

On a host with Docker `linux/arm64` support:

```bash
python scripts/dev.py arm64-setup
python scripts/dev.py arm64-doctor
python scripts/dev.py arm64-test
python scripts/dev.py arm64-demo
python scripts/dev.py arm64-scenario
python scripts/dev.py arm64-benchmark
```

No cloud account, live external source, second board, physical sensor or private credential is required by the H0 Judge flow. The canonical emulator runner uses Docker `--network none`, and guest evidence verifies loopback-only namespace state with no default route before benchmark evidence is admitted.

## Why it matters

Constrained, low-connectivity deployments cannot assume unlimited cloud inference or independent hardware for every monitoring task. Sentinel Edge shows how heterogeneous physical-AI workloads can share one small Arm node while preserving explicit priorities, evidence, source health, uncertainty and fail-visible degradation. The architecture is reusable: hazard science remains separate, while acquisition, scheduling, evidence, incident authority, API and client behavior are shared.

The project also treats reproducibility and claim discipline as product features. Benchmark variants are paired on one opportunity manifest; headline values resolve to machine-readable evidence; replay and simulation are visibly labelled; and a missing sensor or source weakens coverage instead of turning into a misleading “safe” state.

## Significant hackathon-period work

The repository includes `HACKATHON_WORKLOG.md`, release/conformance registries, candidate evidence and generated manifests. The submission materials should reference only work/date claims that resolve to that repository history and the final public candidate.

## Safety and limitations

- Research/decision-support MVP only; not an official warning authority.
- No earthquake prediction.
- No exact monocular wildfire ignition location claim.
- No universal combined disaster probability.
- No physical Raspberry Pi performance/energy/thermal claim from emulation.
- Physical camera/IMU/environmental hardware was not used for the hackathon candidate.
- Collaborative email peer identity is unverified and experimental.
- Flood/landslide H0 behavior is intentionally compact and deterministic rather than overclaiming learned-model science.

## Source and license

The public submission repository is licensed under **Apache-2.0** and contains the source, deterministic fixtures, command surface, UI, tests, benchmark evidence, Claim Registry, rights inventory, Judge Guide and submission-support materials needed for evaluation.
