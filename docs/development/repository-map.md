
# Repository map and authority ownership

| Path | Current owner | Authority rule |
|---|---|---|
| `contracts/` | Shared contract maintainers | Versioned data definitions only; no domain decisions or writable stores. |
| `sdk/` | Shared SDK maintainers | Ports, lifecycle primitives, and test utilities only. |
| `modules/streaming-source-collector/` | Module 01 | Exclusive external/physical source acquisition. |
| `modules/analysis-enrichment-engine/` | Module 02 | Derived claims, lineage, and trust factors; no incident writes. |
| `modules/model-workload-runtime/` | Module 03 | Exclusive release workload execution. |
| `modules/incident-event-engine/` | Module 04 | Exclusive incident lifecycle state writer. |
| `modules/rest-api-integration-gateway/` | Module 05 | Only supported client and third-party mutation boundary. |
| `modules/client-applications/` | Module 06 | Client-only state; no server truth logic or server stores. |
| `apps/` | Composition owners | Wiring and process roots only; no hazard, trust, or incident policy. |
| `integration-tests/` | System verification | Pairwise, vertical, whole-solution, chaos, and release tests. |
| `plugins/` | Plugin artifact owners | Narrow module-scoped implementations governed by manifests. |
| `fixtures/` | Test-data maintainers | Rights-declared deterministic inputs; never production authority. |
| `benchmarks/` | Performance maintainers | Controlled definitions and raw results; no unsupported claims. |
| `provenance/` | Release governance | Capability states, evidence schemas, digests, and acceptance records. |
| `release/` | Release management | Immutable candidate manifests and signed acceptance. |
| `docs/` | Documentation owners | Decisions, baseline, plans, runbooks, and claims. |
| `scripts/` | Delivery engineering | Gate and generation utilities; no domain authority. |
| `.github/workflows/` | Delivery engineering | CI orchestration only. |

I00 implements governance paths and retains the source baseline. Future module directories are created by their owning iteration; absence while `planned` is explicit and is not counted as a passing suite.
