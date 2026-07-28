# Sentinel Edge — Module 05 REST API & Integration Gateway Functional Product Specification

**Document ID:** SE-API-FPD-013  
**Version:** 0.13.0  
**Date:** 2026-07-26  
**Status:** Modular, independently testable product contract  
**Parent documents:** SE-SYS-FPD-013 and SE-SYS-TAS-013  
**Conformance profiles:** `H0` hackathon core, `H1` stretch/hardening, `F1` field-lab, `R` research

> **Research MVP — not an official emergency-warning system. AI observations and forecasts may be wrong. Verify with authorized sources and contact emergency services when appropriate.**

## 1. Purpose and product boundary

Expose the sole supported client and third-party boundary through versioned resources, validated commands, authorization, privacy filtering and resumable projections.

This document defines **what** the module must do, its user-visible and operator-visible behavior, its extension surface, acceptance requirements and independent testability. The paired technical specification defines **how** it is built.

### Primary users

- Web/mobile client developer.
- Operator.
- Integration developer.
- Administrator.

### Inputs

- Incidentprojection/events from module 04.
- Health and diagnostics projections from modules 01–03.
- Client/integration requests.

### Authoritative outputs

- `HTTP resources/responses`.
- `SSE/WebSocket projection events`.
- `OpenAPI document`.
- `audit context`.
- `accepted/rejected IncidentCommand`.

### Explicit non-responsibilities

- It does not own direct database writes to incident state.
- It does not own model invocation.
- It does not own source connector ownership.
- It does not own client-side presentation semantics.
- It does not own inventing projections from raw tables.

## 2. Product principles

1. The module is independently buildable, runnable and testable.
2. The module owns its behavior and persistence; it consumes other modules only through published contracts.
3. A module may be co-located in one process for the MVP, but co-location cannot create internal imports or shared mutable domain state.
4. Test doubles implement the same ports as production adapters.
5. Plugins extend one declared capability; they never become hidden modules or alternate authorities.
6. Missing, stale, invalid, replayed, unauthorized and degraded states remain explicit.
7. Safety, privacy, provenance and quality constraints are not optional plugin concerns.

## 3. Functional capabilities

1. OpenAPI-described REST resources and commands.
2. Idempotency keys, ETags and expected-version optimistic concurrency.
3. Authenticated SSE/WebSocket projections with resume and gap recovery.
4. Privacy/role filtering for exact coordinates, raw media and private source identity.
5. Stable errors using problem details and machine-readable reason codes.
6. Pagination, time/geospatial filters and bounded evidence download.
7. Generated clients and contract fixtures for web/mobile/integrators.

## 4. Core workflows

| Workflow | Required behavior |
|---|---|
| Query | Authenticate → authorize/filter → read projection → ETag/pagination → response. |
| Command | Authenticate → validate schema/idempotency/expected version → emit IncidentCommand → return accepted/result projection. |
| Live projection | Authorize subscription → cursor replay → heartbeat → gap detection → REST resync when required. |
| Export | Authorize purpose/fields → request derived bundle → return immutable manifest and download capability. |

## 5. Extensibility model

The module supports the following extension types:

| Plugin type | Scope |
|---|---|
| AuthProviderPlugin | Authenticates a supported local or deployment identity method. |
| AuthorizationPolicyPlugin | Evaluates scoped actions and field/precision filtering. |
| ProjectionTransportPlugin | Implements SSE/WebSocket/local stream delivery with resume cursors. |
| ExportFormatPlugin | Builds a derived authorized export from immutable references. |
| ReadResourcePlugin | Adds a read-only bounded resource; no plugin receives incident repositories. |
| RateLimitPolicyPlugin | Applies route/identity/resource-specific limits. |

A plugin is product-visible through its capability, provenance, health, limitations and conformance state. A plugin cannot change another module's contracts or bypass the Incident & Event Engine's incident-state authority.

### Plugin governance

1. A plugin belongs to exactly one module API and cannot register itself as a cross-module authority.
2. Discovery may use Python package entry points, but `judge`, `benchmark` and signed `field_lab` configurations load only plugins pinned by ID, version, artifact digest and approved permissions.
3. Plugin activation follows **discover → inspect → verify → compatibility check → instantiate in isolation → self-test → activate → observe → deactivate/rollback**.
4. A plugin receives only narrow module ports, not the composition root, another module repository, raw secrets or unrestricted filesystem/network access.
5. Each plugin ships deterministic conformance fixtures. A plugin is not release-eligible until the owning module's conformance suite passes.
6. Hot installation or code download is disabled in judge/benchmark modes. A plugin change is a release/configuration change and invalidates affected evidence.
7. Plugin failures are contained, counted and surfaced. Repeated failure opens module degradation and disables that plugin without silently replacing semantics.

## 6. Failure and degraded behavior

- REST is authoritative for client state; streaming transports are subordinate projections.
- Filesystem paths, database credentials and internal queue addresses never appear in public contracts.
- API versioning is independent from implementation package versions.
- Unknown or unsupported fields fail according to the declared compatibility policy, not accidental parser behavior.

Every failure produces a stable reason code, affected capability, retryability, operator consequence and recovery rule. “No output” is never treated automatically as “normal” or “safe.”

## 7. Functional requirements

| ID | Priority | Profile | Requirement | Acceptance criterion |
|---|---|---|---|---|
| FR-API-001 | MUST | H0 | Run as an independently packageable REST API & Integration Gateway module. | Module starts with fake external ports and passes black-box health/readiness tests. |
| FR-API-002 | MUST | H0 | Expose only versioned public ports and immutable contract types. | Architecture test detects no imports from another module internal package. |
| FR-API-003 | MUST | H0 | Own its state and migrations. | No direct read/write of another module database or private artifact namespace. |
| FR-API-004 | MUST | H0 | Provide deterministic standalone fixtures and a one-command component test. | `make test-rest-api-integration-gateway` runs without starting the full solution. |
| FR-API-005 | MUST | H0 | Publish producer/consumer schemas and compatibility policy. | Current and declared N-1 golden contracts pass; breaking change is rejected without major version. |
| FR-API-006 | MUST | H0 | Propagate correlation, causation, schema version and producer identity. | A fixture workflow reconstructs every boundary crossing. |
| FR-API-007 | MUST | H0 | Use bounded queues, payload references and explicit failure semantics. | Overload/fault test cannot cause unbounded memory or silent loss. |
| FR-API-008 | MUST | H0 | Support plugin conformance through a stable module SDK. | At least one reference plugin and one deliberately invalid plugin exercise the suite. |
| FR-API-009 | MUST | H0 | Prevent plugins from bypassing module authority or permissions. | Negative test proves denied cross-module repository/network/filesystem access. |
| FR-API-010 | MUST | H0 | Expose health, readiness, metrics and decision/failure reasons. | Module diagnostics distinguish ready, degraded, overloaded and failed. |
| FR-API-011 | MUST | H0 | Participate in pairwise, vertical-slice and whole-solution tests. | CI publishes contract and integration evidence for this module version. |
| FR-API-012 | MUST | H0 | Remain functional under declared offline/degraded conditions. | Standalone degradation scenario produces documented outputs and no false normality. |

## 8. Product metrics

- Contract-valid output ratio and rejected-input count.
- Queue age/depth/high-water and overload duration.
- Plugin health, self-test status and failure containment.
- End-to-end contribution to incident/client visibility where applicable.
- Data-quality, coverage, provenance and trace completeness.
- Standalone component-test duration and flake rate.
- Pairwise contract compatibility status with every declared consumer/provider.

## 9. Independent acceptance package

The module release must contain:

- its own `pyproject.toml`, lock/constraints metadata and package README;
- public port interfaces and generated/schema contract bundle;
- owned migrations or explicit stateless declaration;
- reference in-memory/file/fake adapters;
- deterministic fixtures, golden outputs and conformance suite;
- component runner and health/readiness endpoint or command;
- SBOM fragment and artifact digest;
- compatibility matrix and deprecation notes;
- integration-test stubs for each neighbor.

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

## 10. Definition of done

The module is done only when it passes standalone tests, plugin conformance, schema compatibility, consumer/provider verification, at least one pairwise real integration, the relevant vertical slice and the signed whole-solution scenario. Documentation without executable evidence is `specified`, not `demonstrated`.

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

## 11. Changelog

### 0.13.0 — 2026-07-26

- Split the module from the former monolithic functional document.
- Added independent packaging, owned state and architecture-test requirements.
- Added module-specific plugin types, lifecycle and permission boundaries.
- Added standalone, pairwise, vertical-slice and whole-solution acceptance layers.
