
# ADR-0001: Modular monolith, distributed-capable

- Status: Accepted
- Date: 2026-07-26
- Decision owners: Sentinel Edge architecture

## Context

Sentinel Edge needs compact deployment on Linux Arm64 while preserving independent testing, packaging, owned state, and future process isolation. Shared infrastructure must not become a seventh domain authority.

## Decision

Use six bounded modules behind transport-neutral ports. The default composition is a compact modular monolith; the same public contracts may later cross local framed transports without changing authoritative semantics.

```text
Sources -> [01 Collector] -> [02 Analyzer] <-> [03 Runtime]
                  |                 |               |
                  +-----------------+---------------v
                                      [04 Incident Authority]
                                                |
                                      [05 REST/API Boundary]
                                                |
                                      [06 Web/Mobile Clients]
```

Authority rules:

- Module 01 exclusively acquires external and physical sources.
- Module 03 exclusively executes release workloads.
- Module 04 exclusively writes incident lifecycle state.
- Module 05 is the only supported client/third-party mutation boundary.
- Module 06 never reimplements server truth, policy, or persistence.
- Modules communicate through versioned contracts and public ports, never implementation imports or cross-owned stores.

## Consequences

Compact deployment has low operational overhead. Each module remains independently packageable and testable. Process isolation can be introduced later through adapters. More contracts and boundary tests are required, but hidden coupling is rejected early.
