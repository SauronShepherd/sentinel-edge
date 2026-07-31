
# Sentinel Edge

Sentinel Edge is an edge-first, multi-hazard research platform for collecting observations, analyzing evidence, executing qualified workloads, maintaining authoritative incident state, exposing a public API, and supporting web/mobile operator workflows.

> **Research system, not an official emergency-warning service.** Observations, inferences, forecasts, and demonstrations may be wrong. Always follow authorized sources and emergency services.

## Iteration status

- Baseline: modular architecture documentation v0.13.0
- Active increment: **I02 — six independent module shells and architecture enforcement**
- Completion discipline: an iteration is not complete until every mandatory gate passes with zero unexpected skips, expected failures, collection errors, or flaky reruns.

## Six bounded modules

1. Streaming Source Collector — exclusively acquires source data.
2. Analysis & Enrichment Engine — derives claims, lineage, and trust factors.
3. Model & Workload Runtime — exclusively executes qualified workloads.
4. Incident & Event Engine — exclusively writes incident lifecycle state.
5. REST API & Integration Gateway — only supported client/integration mutation boundary.
6. Client Applications — web/PWA and mobile shells; never reimplement server truth logic.

## First commands

```bash
python scripts/dev.py setup
python scripts/dev.py governance
python scripts/dev.py gates
```

The active I01 gate is intentionally small but real. Targets for future lanes already exist; they validate the capability registry and explicitly report `planned`, without counting absent suites as passing evidence.

## Repository navigation

- `docs/adr/` — accepted architecture and delivery decisions.
- `docs/baseline/v0.13.0/` — immutable source architecture documents and manifest.
- `docs/plans/` — executable end-to-end build plan.
- `provenance/` — capability state, evidence schemas, immutable evidence, and iteration acceptance.
- `scripts/` — repository/governance gate implementations.
- `tests/governance/` — I00 tests and controlled failure proofs.
- `.github/workflows/` — fast, full, and Arm CI contracts.

See [the repository map](docs/development/repository-map.md) for current and planned ownership.
