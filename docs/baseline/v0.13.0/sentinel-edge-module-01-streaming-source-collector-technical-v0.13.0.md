# Sentinel Edge — Module 01 Streaming Source Collector Technical Architecture & Specifications

**Document ID:** SE-COL-TAS-013  
**Version:** 0.13.0  
**Date:** 2026-07-26  
**Status:** Independently deployable/testable module architecture  
**Paired functional document:** SE-COL-FPD-013  
**System integration contract:** SE-SYS-TAS-013

## 1. Architectural decision

Module 01 is a **hexagonal module/bounded context** with a composition root, owned state, public inbound/outbound ports and replaceable adapters. It may run in-process in the compact profile or as an isolated process in the service profile. The same contracts and tests apply to both profiles.

The shared kernel is intentionally small: identifiers, time/quality primitives, immutable contract DTOs, error/problem types, tracing context and test utilities. It contains no hazard, trust, scheduling, persistence or UI business logic.

## 2. Package layout

```text
modules/streaming-source-collector/
├── pyproject.toml
├── README.md
├── src/sentinel_streaming_source_collector/
│   ├── domain/          # pure rules and value objects
│   ├── application/     # use cases and orchestration
│   ├── ports/           # public protocols/interfaces
│   ├── adapters/        # transport, persistence, platform implementations
│   ├── plugins/         # discovery, manifest validation, conformance hooks
│   ├── bootstrap/       # composition root and configuration
│   └── diagnostics/     # health/readiness/metrics
├── contracts/           # schemas/examples/AsyncAPI or OpenAPI fragments
├── migrations/          # owned store only
├── fixtures/            # deterministic standalone and conformance inputs
└── tests/
    ├── unit/
    ├── property/
    ├── component/
    ├── contract/
    ├── plugin_conformance/
    └── nonfunctional/
```

## 3. Public ports

| Port | Responsibility |
|---|---|
| SourceConnectorPort | pull/push/stream acquisition, cursor and health |
| PolicyGatePort | authorize acquisition/retention/analysis |
| NormalizePort | canonical observations/items |
| QuarantinePort | bounded hostile-byte storage |
| CollectorEventPort | emit source contracts |

Ports use immutable DTOs or content-addressed artifact references. No binary media is copied into control messages. Every cross-module envelope includes `id`, `schema_version`, `producer`, `created_at/monotonic`, `correlation_id`, `causation_id`, delivery semantics and optional idempotency key.

## 4. State and data ownership

collector.db plus collector-owned `artifacts/collector/` and `quarantine/`; raw high-rate samples stay in bounded ring/file segments, not per-sample SQL rows.

Rules:

- No SQL joins, filesystem traversal or repository imports cross a module boundary.
- A module may maintain a local read cache/projection only from published events and must tolerate rebuild.
- Schema migration belongs to the module package and is exercised against current and declared N-1 fixtures.
- Artifacts use immutable hashes and owner namespaces. Derived artifacts carry parent hashes and transformation manifests.

## 5. Runtime topology

```text
ModuleRuntime
├── configuration/manifest verifier
├── inbound adapters
├── application services
├── owned repositories/artifact adapters
├── outbound adapters
├── plugin manager
└── health/readiness/metrics
```

The `ModuleRuntime` contract exposes `validate_config()`, `start()`, `readiness()`, `health()`, `drain(deadline)`, `stop()` and `diagnostic_snapshot()`. Tests run the same lifecycle with fake adapters and a virtual clock.

### Collector pipeline

```text
connector → acquisition policy → bounded fetch/read → decoder/parser budget
→ timestamp/sequence/unit/quality normalization → privacy minimization
→ owned ingress ledger/cursor commit → output envelope + source health
```

Cursor commit occurs only after durable owned-state update and output handoff/idempotency registration. A crash may redeliver an item, so consumers must use envelope IDs/idempotency.

## 6. Plugin architecture

| Plugin type | Responsibility | Entry-point group |
|---|---|---|
| SourceConnectorPlugin | Acquires records from one documented source or device interface. | `sentinel.streaming_source_collector.plugins` |
| StreamDecoderPlugin | Decodes one bounded wire/media format into an intermediate record. | `sentinel.streaming_source_collector.plugins` |
| NormalizerPlugin | Maps source fields, units, timestamps and quality into canonical contracts. | `sentinel.streaming_source_collector.plugins` |
| AcquisitionPolicyPlugin | Applies entitlement, rights, privacy, retention and permitted-use rules. | `sentinel.streaming_source_collector.plugins` |
| SensorProtocolPlugin | Implements a versioned physical sensor framing/handshake protocol. | `sentinel.streaming_source_collector.plugins` |
| QuarantineBackendPlugin | Stores hostile external bytes under byte/time/retention limits. | `sentinel.streaming_source_collector.plugins` |

### Manifest

```yaml
plugin_id: sentinel.collector.source.example
plugin_version: 1.0.0
module_api: "1"
entry_point: package.module:factory
capabilities: ["..."]
permissions:
  network: ["none-or-explicit-hosts"]
  filesystem: ["owned-namespace-only"]
  model_execution: false
  incident_write: false
resource_budget:
  cpu_ms_per_item: 0
  rss_bytes: 0
  input_bytes: 0
  wall_time_ms: 0
supported_modes: [development, field_lab]
required_contracts: {sentinel.contract: ">=1,<2"}
fixtures: ["fixtures/conformance.yaml"]
self_test: package.selftest:run
artifact_sha256: "..."
signature_ref: "..."
```

### Plugin governance

1. A plugin belongs to exactly one module API and cannot register itself as a cross-module authority.
2. Discovery may use Python package entry points, but `judge`, `benchmark` and signed `field_lab` configurations load only plugins pinned by ID, version, artifact digest and approved permissions.
3. Plugin activation follows **discover → inspect → verify → compatibility check → instantiate in isolation → self-test → activate → observe → deactivate/rollback**.
4. A plugin receives only narrow module ports, not the composition root, another module repository, raw secrets or unrestricted filesystem/network access.
5. Each plugin ships deterministic conformance fixtures. A plugin is not release-eligible until the owning module's conformance suite passes.
6. Hot installation or code download is disabled in judge/benchmark modes. A plugin change is a release/configuration change and invalidates affected evidence.
7. Plugin failures are contained, counted and surfaced. Repeated failure opens module degradation and disables that plugin without silently replacing semantics.

Plugin dependency resolution is local to the owning module. Plugins cannot depend on another module's implementation package; they may depend only on versioned contract/SDK packages. Circular plugin dependencies are rejected.

## 7. Contracts and compatibility

- Payload schemas use JSON Schema Draft 2020-12.
- Asynchronous channels are documented with AsyncAPI 3.1.0 and stable CloudEvents 1.0.2 envelope semantics.
- Each contract has semantic version, compatibility class, owner, consumers, examples and golden fixtures.
- Additive optional fields are backward compatible; changing meaning, units, requiredness, identity or delivery semantics requires a major version.
- Unknown fields are preserved by relays where practical; security-sensitive unknown commands are rejected.
- Every consumer pins the supported producer contract range and verifies it in CI.

## 8. Error, retry and idempotency model

Errors contain `code`, `category`, `retryable`, `safe_message`, `operator_consequence`, `correlation_id` and optional `details_ref`. Retries are bounded with jitter and never occur for authorization, schema or permanent policy failure. At-least-once inputs use an owned inbox/idempotency record. Replace-latest streams explicitly permit coalescing; best-effort diagnostics never carry incident truth.

## 9. Security and resource containment

- Release plugin/model/config artifacts are allowlisted and digest verified.
- Secrets arrive through narrow credential providers and are never passed wholesale to plugins.
- Network and filesystem permissions are explicit; untrusted parsers/workers are isolated and budgeted.
- Payload bytes, nesting, dimensions, duration, expansion ratio, wall time, RSS and queue age are bounded.
- Logs/metrics avoid private raw payloads and exact restricted coordinates.
- Module shutdown drains only within a deadline; lower-priority work is abandoned safely after recording state.

## 10. Observability

OpenTelemetry-compatible traces, metrics and logs use the same correlation/causation identifiers as contracts. Minimum metrics include input/output count, validation failures, latency stages, queue depth/age/high-water, retries, idempotent duplicates, plugin health, owned-store latency/size and readiness/degradation reasons. Telemetry is batched and cannot endanger critical workloads.

## 11. Testing specification

| # | Mandatory module-specific test |
|---|---|
| 1 | connector conformance tests with success, timeout, malformed payload, rate-limit and entitlement-expiry fixtures |
| 2 | property tests for timestamp ordering, unit conversion, missingness, sequence gaps and deduplication |
| 3 | parser fuzz/resource-budget tests for JSON, XML, archives and media headers |
| 4 | component black-box tests with fake clock, fake transport and temporary owned store |
| 5 | pairwise contract tests against Analyzer, Runtime and Scenario Engine consumers |
| 6 | hardware-in-loop tests for one camera or IMU path and optional sensor-protocol emulator |

### Required test layers

| Layer | Runs without other modules? | Purpose |
|---|---:|---|
| Unit | Yes | Pure rules, transformations, state and edge cases. |
| Property/stateful | Yes | Generated values and operation sequences; invariants and shrinking. |
| Plugin conformance | Yes | Every extension implementation passes the owning module SDK contract. |
| Component black-box | Yes | Start the packaged module with fake ports and verify public behavior. |
| Schema/contract | Yes | JSON Schema, examples, compatibility and generated code. |
| Consumer/provider | Pairwise | Consumer expectations are verified by the real provider. |
| Pairwise integration | Two modules | Real adapters across one boundary, including retries and incompatible versions. |
| Vertical slice | Several modules | One meaningful workflow through its required modules. |
| Whole solution | All modules | Signed simultaneous scenario, failures, recovery and client-visible outcome. |
| Non-functional | Varies | Performance, interference, security, privacy, accessibility and hardware evidence. |

### Standalone test harness

```bash
make test-streaming-source-collector
make component-streaming-source-collector        # starts only this module with fake ports
make conformance-streaming-source-collector      # runs every installed/selected plugin
make contracts-streaming-source-collector        # schemas, examples, compatibility and generated code
```

The black-box harness communicates only through public ports. It must prove startup, readiness, normal behavior, malformed input, timeout, overload, dependency loss, graceful drain, crash/restart and deterministic fixture replay.

## 12. Integration obligations

The module publishes a **provider verification kit** and a **consumer stub kit** for every boundary. CI executes:

1. schema and example validation;
2. consumer expectation generation;
3. provider verification against the real packaged module;
4. incompatible-version negative tests;
5. pairwise real-adapter test;
6. relevant vertical slice;
7. signed whole-solution scenario.

## 13. Performance and release gates

A module release records target architecture, OS/runtime, package/model/plugin/config hashes, cold/warm timings, RSS, queue behavior and invalidation conditions. Performance claims cannot be generated unless quality, contract, host-noise and test gates pass. A plugin added after freeze triggers the owning module and affected integration rerun matrix.

## Source adapter registry and policy contract

Each source plugin is paired with a versioned `SourcePolicyRecord` containing source/authority class, interface and schema version, entitlement owner/status, licence/attribution, permitted acquisition/use/retention, TTL and expected publication latency, spatial/temporal resolution, privacy class, correlation family, circuit-breaker policy, parser budget, benchmark mode and last policy review fingerprint.

Adapter priority for the release is:

1. local camera/IMU/environmental inputs and signed fixture adapters;
2. MeteoAlarm public/entitled route and one authoritative seismic catalogue when stable;
3. bounded metadata/context adapters for FIRMS/EFFIS/GWIS, CEMS, IMERG, ECMWF, EUMETSAT, WIS2, EMSC and GDACS;
4. offline importers for CAMELS-family hydrology, EuroFlood, GLC/UGLC, Tenerife, terrain, soil and hydrography assets;
5. news/platform/WhatsApp adapters only behind documented rights, privacy and optional-feature gates.

Every source plugin test kit includes recorded success/correction/deletion, stale data, schema drift, rate limit, timeout, entitlement expiry, duplicate-origin and correlation-family fixtures. A source whose terms/interface fingerprint expires loses decision influence but does not stop local monitoring.

## Current standards and reference baseline

The release architecture uses standards conservatively: the newest published specification is recorded, while the implementation profile may remain on the newest version supported reliably by the selected tooling.

- OpenAPI Specification 3.2.0 is the latest published OAS (19 September 2025). The Sentinel release profile is OpenAPI 3.1.2 until FastAPI/client-generation/tooling qualification passes for 3.2.0: https://spec.openapis.org/oas/v3.2.0.html
- AsyncAPI Specification 3.1.0 is the event-contract documentation baseline: https://www.asyncapi.com/docs/reference/specification/v3.1.0
- CloudEvents 1.0.2 is the stable event-envelope baseline: https://github.com/cloudevents/spec
- JSON Schema Draft 2020-12 is the payload-schema baseline: https://json-schema.org/draft/2020-12
- OpenTelemetry Specification 1.59.0 and OTLP provide the observability contract baseline: https://opentelemetry.io/docs/specs/otel/
- OGC SensorThings API 1.1 is the stable interoperability mapping target. SensorThings 2.0 remains a candidate/transition topic until formally adopted and tool-qualified: https://www.ogc.org/standards/sensorthings/
- Python plugin discovery uses PyPA entry points, but release modes load only manifest-approved allowlisted plugins: https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
- Consumer/provider contract testing follows the Pact model where useful, with generated OpenAPI/AsyncAPI/schema verification remaining authoritative: https://docs.pact.io/
- Property and state-machine testing uses Hypothesis for boundary values, sequences and lifecycle invariants: https://hypothesis.readthedocs.io/en/latest/stateful.html
- CycloneDX 1.7 is the SBOM/ML-BOM baseline: https://cyclonedx.org/specification/overview/
- SLSA 1.2 is the supply-chain provenance target, without claiming a level that has not been evidenced: https://slsa.dev/

## 14. Changelog

### 0.13.0 — 2026-07-26

- Introduced independently packageable module architecture and owned persistence.
- Added explicit ports/adapters, plugin manifest/lifecycle and conformance test kit.
- Added contract compatibility, inbox/idempotency and black-box component lifecycle tests.
- Added pairwise, vertical-slice and whole-solution integration obligations.
