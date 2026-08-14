# Implementation status

> **Historical snapshot notice (v0.21):** This file is retained as provenance and is not the current hackathon release-status authority. For the active `H0-EMULATED-AARCH64-20260813` candidate, use `docs/release/CURRENT_SUBMISSION_READINESS.md`, `qualification/g0-gate-status.json`, and the exact release-candidate evidence. Physical Raspberry Pi/sensor qualification described below is post-submission/reference-target work for this profile.


**Version:** 0.21.0  
**Contract basis:** Sentinel Edge full-scope product and technical contracts v0.22.0  
**Framework:** native contract/registry governance

Version 0.21.0 adds one generated qualification vocabulary and claim ceiling, explicit evidence windows with expiry consequences, a platform runtime-envelope contract, richer benchmark-host snapshots and a cold/session known-answer runtime gate. These controls prove fail-closed development semantics. They do not qualify a Raspberry Pi host, physical signal path, target runtime or field site.

## Current source truth

| State | Count |
|---|---:|
| `IMPLEMENTED` | 569 |
| `CONFIRMED` | 174 |
| `VERIFIED` | 0 |
| Total | 743 |

Of the 240 H0 requirements, 238 are `IMPLEMENTED` and 2 remain open. No target, field or release verification is claimed.

The H1 controlled-activity path is now implemented at Component 4: the operator
command records a `control` label, preserves the incident state, and retries are
idempotently suppressed without creating a duplicate version.

## Newly executable in v0.21.0

### Qualification vocabulary and claim ceiling

- Uses the closed `CapabilityState` vocabulary for machine-readable qualification records.
- Rejects unknown states through typed validation.
- Computes the weakest effective evidence state across platform, source, model, calibration and security evidence.
- Rejects claims stronger than the weakest evidence state.
- Keeps expired, blocked, failed and reconstructed evidence from supporting qualified claims.

The generated conformance ledger now records explicit artifact references and a
per-requirement deferral reason, so absent target evidence is visible rather
than inferred from an empty list.

### Evidence windows and historical-proof limits

- Every qualification record has a domain, subject, evidence digest, validity start, validity end, provenance and target binding.
- Expired evidence becomes `expired` and immediately blocks the affected claim.
- Future-dated evidence is blocked until valid.
- Migrated or reconstructed evidence must state the missing historical fields and cannot invent target, field or release qualification.

### Platform runtime envelope

- Binds board, bootloader, firmware, kernel, OS/root identity, CPU features, runtime, provider, drivers, hardening, benchmark-host and host-trust evidence.
- Missing or incompatible platform facts prevent a host from inheriting prior target qualification.
- Explicitly rejects SVE, SVE2, SME or SME2 claims for a Raspberry Pi 5 target.
- Distinguishes observed target facts from fixture envelopes.

### Host and idle/noise evidence

- Benchmark host observations now include CPU governor/frequency, IRQ affinity, process affinity/cpuset, cgroup identity, CPU/memory/I/O PSI, page-cache/writeback, major faults and a bounded process snapshot.
- Idle/noise qualification covers load, CPU/memory/I/O pressure, dirty/writeback pages and major-fault deltas.
- Out-of-envelope samples receive explicit invalidation reasons.

### Runtime known-answer gate

- Repeats cold/session initialization before service start.
- Executes exact named-output and shape checks with tolerance-bound known answers.
- Requires declared branch coverage.
- Fails service startup on initialization exception, execution failure, output mismatch or missing branch.
- Keeps development success separate from target-host and target-runtime qualification.

### Release and CLI closure

- Candidate qualification now requires a target-qualified platform envelope, valid qualification-window claim and target-qualified runtime known-answer report.
- Added CLI commands for qualification-window, claim-ceiling and platform-envelope evaluation.
- All new reports are bound into provenance and candidate identity.

## Current release truth

The repository remains a development candidate. The included platform envelope is a fixture/development envelope, qualification windows cap claims at `tested`, and the known-answer suite uses a deterministic fixture adapter. Raspberry Pi host evidence, physical signal capture, target ONNX Runtime/provider execution, target model quality, field commissioning, measured B0/B1/O1 evidence, independent reviews and 2 H0 requirements remain open.
