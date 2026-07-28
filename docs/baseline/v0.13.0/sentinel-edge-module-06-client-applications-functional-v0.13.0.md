# Sentinel Edge — Module 06 Client Applications — Web + Mobile Functional Product Specification

**Document ID:** SE-CLI-FPD-013  
**Version:** 0.13.0  
**Date:** 2026-07-26  
**Status:** Modular, independently testable product contract  
**Parent documents:** SE-SYS-FPD-013 and SE-SYS-TAS-013  
**Conformance profiles:** `H0` hackathon core, `H1` stretch/hardening, `F1` field-lab, `R` research

> **Research MVP — not an official emergency-warning system. AI observations and forecasts may be wrong. Verify with authorized sources and contact emergency services when appropriate.**

## 1. Purpose and product boundary

Deliver one coherent, accessible and offline-aware operator experience through independently buildable web and mobile shells using the same generated contracts and domain semantics.

This document defines **what** the module must do, its user-visible and operator-visible behavior, its extension surface, acceptance requirements and independent testability. The paired technical specification defines **how** it is built.

### Primary users

- Local monitoring operator.
- Field reviewer.
- Deployment technician.
- Hackathon evaluator.

### Inputs

- Rest resources and authenticated live projections from module 05.
- Local device capabilities for mobile capture/notifications.

### Authoritative outputs

- `API commands`.
- `upload/capture requests`.
- `local notification actions`.
- `client telemetry and accessibility evidence`.

### Explicit non-responsibilities

- It does not own direct incident-state mutation.
- It does not own direct database or filesystem access.
- It does not own reimplementing server trust/state logic.
- It does not own loading arbitrary third-party JavaScript/plugins.
- It does not own hiding degraded coverage.

## 2. Product principles

1. The module is independently buildable, runnable and testable.
2. The module owns its behavior and persistence; it consumes other modules only through published contracts.
3. A module may be co-located in one process for the MVP, but co-location cannot create internal imports or shared mutable domain state.
4. Test doubles implement the same ports as production adapters.
5. Plugins extend one declared capability; they never become hidden modules or alternate authorities.
6. Missing, stale, invalid, replayed, unauthorized and degraded states remain explicit.
7. Safety, privacy, provenance and quality constraints are not optional plugin concerns.

## 3. Functional capabilities

1. Mission control, four hazard views, incident timeline and evidence review.
2. Consistent trust dimensions, source modes, coverage and safety language.
3. Offline read cache and idempotent queued actions with conflict visibility.
4. Responsive web/PWA and mobile/native shell using shared domain types.
5. Field capture/upload with consent, privacy and progress/failure states.
6. Keyboard/screen-reader/reduced-motion/text-equivalent support.
7. Judge proof, benchmark and diagnostics views generated from authoritative data.

## 4. Core workflows

| Workflow | Required behavior |
|---|---|
| Mission control | Load cached shell → fetch projections → subscribe → render event and system health independently. |
| Review | Open incident/evidence → inspect provenance/trust → issue idempotent command → show pending/accepted/conflict. |
| Offline action | Queue with command/idempotency/version metadata → reconnect → submit → resolve duplicate/conflict visibly. |
| Field report | Capture → preview/privacy notice → upload through API → track quarantine/analysis status. |

## 5. Extensibility model

The module supports the following extension types:

| Plugin type | Scope |
|---|---|
| EvidenceRendererPlugin | Renders an allowlisted evidence modality/type using sanitized data. |
| CaptureProviderPlugin | Captures/uploads one supported mobile/web modality under privacy policy. |
| NotificationAdapterPlugin | Maps server intents to a local notification channel. |
| LocalizationPackPlugin | Provides versioned translations and terminology tests. |
| ReadOnlyPanelPlugin | Adds a bounded view over published API data; no arbitrary remote code. |
| OfflineStorePlugin | Implements encrypted/local cache storage behind one interface. |

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

- Web and mobile may differ in interaction design but cannot diverge in incident semantics.
- No color-only severity or motion-only scheduler explanation.
- Cached data always shows age, source mode and connection state.
- Client plugin bundles are build-time or signed/allowlisted; judge mode has no dynamic plugin download.

Every failure produces a stable reason code, affected capability, retryability, operator consequence and recovery rule. “No output” is never treated automatically as “normal” or “safe.”

## 7. Functional requirements

| ID | Priority | Profile | Requirement | Acceptance criterion |
|---|---|---|---|---|
| FR-CLI-001 | MUST | H0 | Run as an independently packageable Client Applications — Web + Mobile module. | Module starts with fake external ports and passes black-box health/readiness tests. |
| FR-CLI-002 | MUST | H0 | Expose only versioned public ports and immutable contract types. | Architecture test detects no imports from another module internal package. |
| FR-CLI-003 | MUST | H0 | Own its state and migrations. | No direct read/write of another module database or private artifact namespace. |
| FR-CLI-004 | MUST | H0 | Provide deterministic standalone fixtures and a one-command component test. | `make test-client-applications` runs without starting the full solution. |
| FR-CLI-005 | MUST | H0 | Publish producer/consumer schemas and compatibility policy. | Current and declared N-1 golden contracts pass; breaking change is rejected without major version. |
| FR-CLI-006 | MUST | H0 | Propagate correlation, causation, schema version and producer identity. | A fixture workflow reconstructs every boundary crossing. |
| FR-CLI-007 | MUST | H0 | Use bounded queues, payload references and explicit failure semantics. | Overload/fault test cannot cause unbounded memory or silent loss. |
| FR-CLI-008 | MUST | H0 | Support plugin conformance through a stable module SDK. | At least one reference plugin and one deliberately invalid plugin exercise the suite. |
| FR-CLI-009 | MUST | H0 | Prevent plugins from bypassing module authority or permissions. | Negative test proves denied cross-module repository/network/filesystem access. |
| FR-CLI-010 | MUST | H0 | Expose health, readiness, metrics and decision/failure reasons. | Module diagnostics distinguish ready, degraded, overloaded and failed. |
| FR-CLI-011 | MUST | H0 | Participate in pairwise, vertical-slice and whole-solution tests. | CI publishes contract and integration evidence for this module version. |
| FR-CLI-012 | MUST | H0 | Remain functional under declared offline/degraded conditions. | Standalone degradation scenario produces documented outputs and no false normality. |

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
