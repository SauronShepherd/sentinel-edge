# Sentinel Edge — Module 01 Streaming Source Collector Functional Product Specification

**Document ID:** SE-COL-FPD-013  
**Version:** 0.13.0  
**Date:** 2026-07-26  
**Status:** Modular, independently testable product contract  
**Parent documents:** SE-SYS-FPD-013 and SE-SYS-TAS-013  
**Conformance profiles:** `H0` hackathon core, `H1` stretch/hardening, `F1` field-lab, `R` research

> **Research MVP — not an official emergency-warning system. AI observations and forecasts may be wrong. Verify with authorized sources and contact emergency services when appropriate.**

## 1. Purpose and product boundary

Acquire, validate, normalize and safely stage heterogeneous physical, official, scientific, publisher, authorized-platform, opt-in community and fixture inputs without deciding incident truth.

This document defines **what** the module must do, its user-visible and operator-visible behavior, its extension surface, acceptance requirements and independent testability. The paired technical specification defines **how** it is built.

### Primary users

- Deployment technician.
- Source integration developer.
- Data steward.
- Scenario/benchmark author.

### Inputs

- Physical sensors and cameras.
- Official/scientific apis and feeds.
- Publisher rss/atom/apis.
- Authorized platform webhooks/metadata.
- Operator/community uploads.
- Signed fixtures and scenario streams.

### Authoritative outputs

- `ObservationEnvelope`.
- `ExternalSourceItem`.
- `SourceHealthEvent`.
- `AcquisitionAuditEvent`.

### Explicit non-responsibilities

- It does not own extracting semantic incident claims.
- It does not own running release ML models directly.
- It does not own creating or mutating incidents.
- It does not own serving client APIs.

## 2. Product principles

1. The module is independently buildable, runnable and testable.
2. The module owns its behavior and persistence; it consumes other modules only through published contracts.
3. A module may be co-located in one process for the MVP, but co-location cannot create internal imports or shared mutable domain state.
4. Test doubles implement the same ports as production adapters.
5. Plugins extend one declared capability; they never become hidden modules or alternate authorities.
6. Missing, stale, invalid, replayed, unauthorized and degraded states remain explicit.
7. Safety, privacy, provenance and quality constraints are not optional plugin concerns.

## 3. Functional capabilities

1. Continuous and scheduled acquisition with backpressure, jitter and circuit breakers.
2. Capture/sample time, ingest time, sequence, boot ID, unit and clock-quality preservation.
3. Source-policy and licence/entitlement enforcement before byte retrieval or persistence.
4. Source-level duplicate detection, replay labeling and event-time watermarks.
5. Pre-persistence privacy masks and coordinate minimization.
6. Deterministic fixture/scenario mode using the same ports as live connectors.
7. Fault-visible source health without blocking local physical sensing.

## 4. Core workflows

| Workflow | Required behavior |
|---|---|
| Physical stream | Capture → timestamp/sequence validation → unit normalization → quality assessment → observation emission. |
| Remote structured source | Schedule/webhook → policy gate → fetch → schema/parser budget → normalize → cursor commit → source item emission. |
| External media | Lead/upload → rights/privacy gate → quarantine → metadata envelope; analysis occurs only in Module 02. |
| Fixture replay | Signed scenario → deterministic clock → same connector/normalizer interfaces → transcript. |

## 5. Extensibility model

The module supports the following extension types:

| Plugin type | Scope |
|---|---|
| SourceConnectorPlugin | Acquires records from one documented source or device interface. |
| StreamDecoderPlugin | Decodes one bounded wire/media format into an intermediate record. |
| NormalizerPlugin | Maps source fields, units, timestamps and quality into canonical contracts. |
| AcquisitionPolicyPlugin | Applies entitlement, rights, privacy, retention and permitted-use rules. |
| SensorProtocolPlugin | Implements a versioned physical sensor framing/handshake protocol. |
| QuarantineBackendPlugin | Stores hostile external bytes under byte/time/retention limits. |

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

- A malformed remote item cannot block physical sensor capture.
- Every queue and parser has a declared capacity, byte limit, age limit and drop/coalesce policy.
- No live connector is required for judge, benchmark or offline operation.
- A stale or replayed item cannot masquerade as a fresh observation.

Every failure produces a stable reason code, affected capability, retryability, operator consequence and recovery rule. “No output” is never treated automatically as “normal” or “safe.”

## 7. Functional requirements

| ID | Priority | Profile | Requirement | Acceptance criterion |
|---|---|---|---|---|
| FR-COL-001 | MUST | H0 | Run as an independently packageable Streaming Source Collector module. | Module starts with fake external ports and passes black-box health/readiness tests. |
| FR-COL-002 | MUST | H0 | Expose only versioned public ports and immutable contract types. | Architecture test detects no imports from another module internal package. |
| FR-COL-003 | MUST | H0 | Own its state and migrations. | No direct read/write of another module database or private artifact namespace. |
| FR-COL-004 | MUST | H0 | Provide deterministic standalone fixtures and a one-command component test. | `make test-streaming-source-collector` runs without starting the full solution. |
| FR-COL-005 | MUST | H0 | Publish producer/consumer schemas and compatibility policy. | Current and declared N-1 golden contracts pass; breaking change is rejected without major version. |
| FR-COL-006 | MUST | H0 | Propagate correlation, causation, schema version and producer identity. | A fixture workflow reconstructs every boundary crossing. |
| FR-COL-007 | MUST | H0 | Use bounded queues, payload references and explicit failure semantics. | Overload/fault test cannot cause unbounded memory or silent loss. |
| FR-COL-008 | MUST | H0 | Support plugin conformance through a stable module SDK. | At least one reference plugin and one deliberately invalid plugin exercise the suite. |
| FR-COL-009 | MUST | H0 | Prevent plugins from bypassing module authority or permissions. | Negative test proves denied cross-module repository/network/filesystem access. |
| FR-COL-010 | MUST | H0 | Expose health, readiness, metrics and decision/failure reasons. | Module diagnostics distinguish ready, degraded, overloaded and failed. |
| FR-COL-011 | MUST | H0 | Participate in pairwise, vertical-slice and whole-solution tests. | CI publishes contract and integration evidence for this module version. |
| FR-COL-012 | MUST | H0 | Remain functional under declared offline/degraded conditions. | Standalone degradation scenario produces documented outputs and no false normality. |

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

## Source and dataset registry owned by this module

The Collector owns source adapter registration and source policy, but **source role controls decision influence**. A technically reachable source is disabled until access, licence/terms, attribution, freshness, geographic resolution, correlation family and retention are recorded.

| Class | Candidate sources | Permitted role |
|---|---|---|
| T0 local physical | camera, IMU, rainfall, water level, soil moisture, tilt, vibration | direct local observation subject to calibration, health and coverage |
| T1 official/authoritative | MeteoAlarm/AEMET where entitled, IGN, USGS FDSN, EMSC/SeismicPortal, jurisdictional CAP feeds | official status or post-onset corroboration within scope; original wording preserved |
| T2 operational scientific context | NASA FIRMS, EFFIS, GWIS, CEMS Global Flood Monitoring/Rapid Mapping, GPM IMERG, ECMWF Open Data, EUMETSAT MTG fire/lightning, WIS 2.0 discovery, GDACS | asynchronous context, priority/cadence input or later corroboration; never local sensor truth |
| T3 research/historical | CAMELS-ES, BULL, Caravan, LamaH-CE, EStreams, EuroFlood, NASA GLC, UGLC, Tenerife multi-hazard dataset, terrain/soil/hydrography datasets | offline training, evaluation, fixture/scenario design and susceptibility context only |
| T4 opportunistic | professional news, identified eyewitness reports, pseudonymous/anonymous posts, authorized platform leads, opt-in WhatsApp reports | display, lead and bounded review/cadence priority; never sole verification or resolution |

Correlation is provenance-aware: FIRMS-derived EFFIS/GWIS items, copied articles, reposts and catalogues sharing one underlying event solution do not count as independent confirmations. Large raster/archive datasets are clipped and prepared offline; the edge hot path never downloads full global products.

Reference sources include: https://api.meteoalarm.org/ , https://earthquake.usgs.gov/fdsnws/event/1/ , https://www.seismicportal.eu/ , https://firms.modaps.eosdis.nasa.gov/ , https://effis.jrc.ec.europa.eu/ , https://gwis.jrc.ec.europa.eu/ , https://gpm.nasa.gov/data/imerg , https://www.ecmwf.int/en/forecasts/datasets/open-data , https://github.com/nasa/LHASA , https://essd.copernicus.org/articles/18/4697/2026/ and https://essd.copernicus.org/articles/18/2979/2026/ .

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
