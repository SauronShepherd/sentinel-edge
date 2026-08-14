# Sentinel Edge — Five-Minute Judge Guide

> **Research MVP — not an official emergency-warning system.** AI observations and forecasts may be wrong. Verify with authorized sources and contact emergency services when appropriate.

## What to understand in 30 seconds

Sentinel Edge is an offline-first Physical AI platform that runs **exactly four** hazard-monitoring workloads — wildfire, earthquake, flood and landslide — on one constrained Arm64 edge target. Its differentiator is the **Arm AI Orchestrator**: criticality/deadline scheduling protects the Tier-A earthquake path, wakes/sleeps heavier wildfire processing, adapts flood/landslide cadence, bounds queues and exposes overload/degradation instead of hiding it.

The hackathon release profile is `H0-EMULATED-AARCH64-20260813`. Arm execution is reproduced in Docker/QEMU `linux/arm64`; all camera, IMU and environmental signals are deterministic simulations/fixtures entering through the normal Component-1 observation contract. Physical Raspberry Pi or sensor hardware is not required, and the project makes **no Raspberry Pi 5 performance, energy, thermal or physical-sensor-quality claim** from emulated results.

The architecture has exactly six top-level components. **Component 4 — Incident & Event Engine — is the sole incident-lifecycle mutation authority.**

## Fastest no-hardware path

From the repository root:

```bash
python scripts/dev.py setup
python scripts/dev.py doctor
python scripts/dev.py demo
```

These commands require no cloud account, API key, live source, second board or physical sensor. `setup` uses a normal site-packages `.pth` to make the checkout importable without a `PYTHONPATH` environment workaround. For ordinary local Judge/demo use it may reuse an already-installed compatible environment and records that fact in `.tmp/setup-environment.json`; the final `submission-preflight` requires the exact hash-pinned `requirements-dev.lock.txt` and does not allow that compatibility fallback.

### Open the actual local product UI

```bash
python scripts/dev.py ui
```

Then open:

```text
http://127.0.0.1:8000/client
```

For the local development/Judge read-only session, use:

```text
sentinel-dev-viewer-token
```

The UI command resets local demo state, runs the deterministic simultaneous-event fixture through normal product boundaries, then serves the seeded PWA on loopback. The page remains inspectable without authentication using clearly labelled fixture/demo values; connecting the local viewer session upgrades it to live Component-5 projections.

Recommended UI tour:

1. **Overview** — four hazards, health/coverage, scheduler and release identity.
2. **Mission Control** — all four hazard cards, evidence, uncertainty, review, running/queued/sleeping/deferred jobs and state-change reasons.
3. **Incidents** — three-column incident/evidence/review workspace; verify Component-4 authority wording.
4. **Benchmark Lab** — B0/B1/O1 absolute values, fairness guardrails and the emulated-performance disclaimer.
5. **Judge Proof** — all twelve G0 packs, H0 closure and canonical commands.
6. **Collaboration** — optional H1 feature, default OFF, separate sharing/research consent, simulated peer proof and `email_unverified` boundary.

## Deeper deterministic proof

```bash
python scripts/dev.py verify
python scripts/dev.py scenario
python scripts/dev.py test-all
python scripts/dev.py gates
python scripts/dev.py benchmark-replay
python scripts/dev.py claims
```

Expected evidence includes the scenario transcript/invariants, opportunity accounting, G0 status, H0 closure, Claim Registry and B0/B1/O1 raw artifacts. The current simultaneous-event proof evaluates **24 executable invariants**, including the four hazard inputs, Tier-A-first dispatch, wildfire wake/sleep, adaptive flood/landslide cadence, bounded queues, deferral/overload, source and sensor failure, deterministic worker crash/recovery, replay/backfill freshness protection, evidence creation, Component-4 authority, and a four-hazard read through the local Component-5 REST projection. Its machine-readable artifacts are written under `.tmp/scenario-proof/` and copied into the Judge package as simulated/fixture evidence. Mandatory acceptance lanes fail closed on zero tests/items, unexpected skips/xfails, stale candidate evidence or invalid claim bindings.

## Canonical Arm64-emulated execution path

On a machine with Docker capable of `linux/arm64` execution:

```bash
python scripts/dev.py arm64-setup
python scripts/dev.py arm64-doctor
python scripts/dev.py arm64-test
python scripts/dev.py arm64-demo
python scripts/dev.py arm64-scenario
python scripts/dev.py arm64-benchmark
```

`arm64-doctor` must identify the **guest** as AArch64 separately from the host, report Python and ONNX Runtime identity/providers, source/fixture/config hashes and the lack of physical sensors. `arm64-benchmark` refuses to run outside an Arm64 guest. The canonical base is immutable at `python:3.13.15-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a`; the generated Arm64 lock pins the full Judge/test environment and exact AArch64 inference-runtime artifacts. `config/arm64-python-artifacts.json` records the publisher-index wheel filenames and SHA-256 values for NumPy, Protobuf, FlatBuffers and ONNX Runtime, and the Docker build installs with `--require-hashes --only-binary=:all:`. Doctor and benchmark create a real ONNX Runtime session with `CPUExecutionProvider`, execute the release model known-answer (`0.5`), reject unexpected provider fallback, bind the installed distribution `RECORD` and native-library hashes, and record the resolved local Docker image ID. The canonical runner also uses Docker `--network none`; the guest must observe loopback-only namespace state with no default route before the Arm64 doctor/benchmark lane passes.

## Optimization proof

The bundled emulated benchmark uses one deterministic opportunity schedule for all variants:

| Variant | Meaning | Median semantic E2E | p95 | Deadline misses |
|---|---|---:|---:|---:|
| `B0` | Naive fixed-rate baseline | 111.5 ms | 137 ms | 3 |
| `B1` | Optimized runtime, fixed-rate | 80.5 ms | 97 ms | 1 |
| `O1` | Optimized runtime + orchestrator | 69.0 ms | 97 ms | 0 |

The Claim Registry classifies the headline semantic results as **`simulated`**. Under the retained deterministic Arm64-emulated workload, O1 reduces the semantic median by 42.5 ms relative to B0 and preserves the declared quality guardrails. The final benchmark schema additionally records total service/queue delay, heavy-workload invocation and duty-cycle accounting, explicit `simulated` labels for thermal/power/resource-policy inputs, and a separate scheduler-control-plane CPU-overhead measurement made inside the AArch64 guest. These values are **not Raspberry Pi 5 measurements** and do not imply identical native-hardware deltas.

## Exactly six components

| # | Component | Authority |
|---:|---|---|
| 1 | Streaming Source Collector | acquisition/quarantine/normalized observations |
| 2 | Analysis & Enrichment Engine | analysis outputs, never incident state |
| 3 | Model & Workload Runtime | validated execution + scheduling |
| 4 | Incident & Event Engine | **sole incident lifecycle authority** |
| 5 | REST API & Integration Gateway | supported client/integration boundary |
| 6 | Client Applications | projections and user commands through Component 5 |

## Truth labels

- `fixture` — bundled deterministic input exercised through production contracts.
- `simulated` — generated physical/scheduling behavior; not physical-device evidence.
- `replayed` — previously captured/signed result being inspected again.
- `live` — current source data where an optional source is actually enabled and qualified.
- Claim classes: `measured`, `replayed`, `simulated`, `target`, `research`. This H0 emulator benchmark is `simulated`.

Replay/backfill can never silently become fresh evidence. Monitoring coverage and system health are separate from hazard state.

## Collaborative Detection

Collaborative Detection is optional H1/S8 and disabled by default. Offline proof requires no Gmail:

```bash
python scripts/dev.py collaboration-check
python scripts/dev.py collaboration-demo
python scripts/dev.py collaboration-gmail-fixture
python scripts/dev.py test-collaboration
```

Only compact, privacy-coarsened event signals may be shared after opt-in. Raw camera/video/audio/IMU/water/soil/tilt streams, exact coordinates, user identities and credentials are excluded. `email_unverified` transport may create experimental review context but is not cryptographic peer identity and cannot create trusted real multi-node confirmation. The local implementation includes hazard-aware privacy transformation, material-event signal generation, bounded SMTP retry/suppression, durable Gmail receipt idempotency, a module-owned SQLite correlation repository option, low-cardinality metrics, Component-4 independent-peer correlation, and the full deterministic JSON/`.eml` negative-fixture matrix.

Mission Control contains the collaboration status card required by the UI specification. The Collaboration workspace exposes operational sharing and separate research consent, all four hazard selectors, the exact shared/not-shared privacy disclosure, transport trust, and the explicit Experimental / Default OFF / not-an-official-warning boundary. Incident details show local versus collaborative evidence without a single opaque collaborative truth percentage.

## Candidate and package verification

Before the final submission freeze, run the full preflight on the exact Git revision in an environment where Docker/QEMU Arm64 is available:

```bash
python scripts/dev.py submission-preflight
python scripts/dev.py release-candidate
```

The candidate builder binds repository identity, contracts, H0/G0 status, runtime/config/fixture/model identities, Claim Registry, benchmark evidence, Judge package and command matrix. Candidate-affecting changes after freeze require a new candidate/rerun set.

After release admission, run `python scripts/dev.py package`. For an admitted candidate this command automatically copies the Judge package into an isolated temporary environment, runs the local Judge smoke path, and verifies imports resolve from that copied package rather than any stale editable checkout.

## Where to inspect artifacts

- `qualification/emulated-arm64-benchmark.json` — Arm64-emulated B0/B1/O1 evidence.
- `qualification/g0-gate-status.json` — generated G0 gate packs.
- `qualification/claim-registry.json` — public claim ceiling and evidence refs.
- `qualification/release-minimum-manifest.json` — H0 cutline closure.
- `qualification/uix-conformance.json` — machine-readable UIX conformance across the ten reference-screen families and persistent truth/safety surfaces.
- `provenance/evidence/` — command/evidence receipts.
- `provenance/submission-media/` — screenshot/video manifests.
- `docs/release/CURRENT_SUBMISSION_READINESS.md` — generated readiness summary.
- `docs/design/` — UIX specification and design-reference mockups; **not runtime evidence**.

## Final human-only actions

After the exact final preflight/candidate is green: publish the repository, capture the real candidate screenshots/video, upload the sub-three-minute video, insert final URLs on Devpost and submit. Do not use the generated UI reference mockups as product evidence.

## Complete public command catalogue

`architecture/command-catalog.yaml` is the machine-readable authority. The additional focused maintenance/verification lanes are available as `python scripts/dev.py <command>`:

```text
setup doctor verify ui uix demo scenario benchmark benchmark-replay claims gates test-all aer
format lint type architecture governance contracts no-silent-skips hygiene
plugins testkit components clients packages compatibility generated
security privacy accessibility provenance docs report package backup-verify update-verify test-arm
submission-preflight release-candidate
arm64-setup arm64-doctor arm64-test arm64-demo arm64-scenario arm64-benchmark
collaboration-check collaboration-demo collaboration-gmail-fixture test-collaboration
```

The short Judge workflow does not require running every maintenance lane individually; release preflight/gates select the mandatory acceptance set for the frozen candidate.
