# Sentinel Edge — Complete End-to-End Build Plan

**Plan ID:** SE-BUILD-PLAN-013  
**Baseline:** Sentinel Edge modular documentation v0.13.0  
**Date:** 2026-07-26  
**Status:** Executable implementation plan  
**Delivery model:** Atomic tasks → functional stages → gated iterations

> **Research system, not an official emergency-warning service.** AI observations, inferences and forecasts may be wrong. Product language, tests and demonstrations must preserve this limitation and direct users to authorized sources and emergency services when appropriate.

## 1. Purpose

This plan turns the v0.13.0 six-module architecture into a step-by-step build sequence:

- a **task** creates or modifies one primary file only;
- a **stage** groups related tasks across different files to deliver one coherent outcome;
- an **iteration** groups stages that add, extend or harden a usable capability;
- every iteration ends with a complete regression gate and remains **in progress** until every mandatory test passes.

The plan preserves the system invariants: Module 01 exclusively acquires sources; Module 03 exclusively executes release workloads; Module 04 exclusively writes incident lifecycle state; Module 05 is the only supported client and third-party mutation boundary; Module 06 never reimplements server truth logic; shared infrastructure never becomes a seventh domain authority.

## 2. Work-item rules

### 2.1 Atomic task rule

Each task has exactly one `Primary file`. A task may read contracts and invoke tests, but its implementation modification is confined to that file. A change requiring two files is split into two tasks in the same stage. Generated outputs have a dedicated generator task and a separate drift-verification task.

A task is complete only when its one-file change is reviewed, its targeted verification passes, no unrelated file is modified, traceability is recorded, and it introduces no unexpected skip, expected failure, warning suppression or flaky rerun.

### 2.2 Stage rule

A stage is complete only when all its tasks pass and their cross-file behavior is verified through public ports or generated contracts. Code review alone never completes a stage.

### 2.3 Iteration rule

An iteration is complete only after its entire regression gate passes. A failure creates one-file remediation tasks inside the same iteration. Run targeted checks first, then the stage checks, then the **entire iteration gate**. Never convert a failure into a skip or waiver to finish an iteration.

### 2.4 Capability states

| State | Meaning | Release treatment |
|---|---|---|
| `planned` | Future work is listed but is not an active product claim. | It cannot be counted as passing. |
| `active` | Implementation and mandatory tests are required in every relevant gate. | Not releasable until demonstrated. |
| `demonstrated` | All required evidence is green and current for exact hashes. | Releasable subject to system gates. |
| `retired` | Removed through explicit compatibility, migration and regression evidence. | Not active. |

## 3. Target repository structure

```text
sentinel-edge/
├── pyproject.toml
├── uv.lock
├── Makefile
├── contracts/sentinel-contracts/
├── contracts/compatibility-matrix/
├── sdk/sentinel-plugin-sdk/
├── sdk/sentinel-testkit/
├── modules/streaming-source-collector/
├── modules/analysis-enrichment-engine/
├── modules/model-workload-runtime/
├── modules/incident-event-engine/
├── modules/rest-api-integration-gateway/
├── modules/client-applications/
├── apps/sentinel-node/
├── apps/sentinel-module-runner/
├── apps/sentinel-scenario-runner/
├── integration-tests/
├── plugins/
├── fixtures/
├── benchmarks/
├── provenance/
├── release/
└── docs/
```

## 4. Global definition of done

A capability is `demonstrated`, not merely `specified`, only when all applicable evidence exists:

- immutable versioned contracts, examples and current/N-1 compatibility;
- unit and property/state-machine tests for pure rules and lifecycle invariants;
- plugin conformance, including a deliberately invalid implementation;
- packaged component black-box tests with fake ports and temporary owned state;
- real consumer/provider verification and incompatible-version negatives;
- pairwise integration through real adapters for every declared boundary;
- relevant vertical slices and signed whole-solution scenarios;
- overload, crash, retry, restart, offline and recovery behavior;
- security, privacy, accessibility and supply-chain evidence;
- target Arm quality/performance evidence before any performance claim;
- current documentation, SBOM/ML-BOM, provenance and release bill.

## 5. Standard end-of-iteration gate

Every iteration runs this sequence. Suites for capabilities still marked `planned` are excluded by the capability registry, not counted as passing. Once activated, a suite remains mandatory forever unless the capability is explicitly retired.

```text
1. clean workspace and dependency-lock verification
2. formatting, linting and static/type analysis
3. architecture ownership/import/path/authority tests
4. all active module unit and property/state-machine tests
5. all active plugin conformance and permission/resource tests
6. schemas, examples, generated bindings and compatibility tests
7. all active packaged component black-box tests
8. all active consumer/provider verifications
9. all active pairwise integrations
10. every previously activated vertical slice
11. current signed whole-solution scenarios
12. active chaos, restart, offline and recovery tests
13. active security, privacy and accessibility tests
14. active target-Arm hardware and benchmark gates
15. claims, provenance, SBOM, documentation and evidence validation
16. unexpected-skip/xfail/flaky/collection-error scan
17. aggregate `make gates`
```

Recommended command surface:

```bash
make setup
make format-check lint type architecture
make test-all-modules
make plugins contracts components
make consumer-provider pairwise slices scenario chaos
make security privacy accessibility
make test-arm benchmark
make provenance docs
make gates
```

## 6. Failure protocol

When any check fails:

1. preserve logs, seed, environment, transcript and artifact hashes;
2. classify it as product defect, test defect, environment defect or specification conflict;
3. create one or more one-primary-file remediation tasks inside the same iteration;
4. add or strengthen a regression test before or with the fix;
5. run targeted, stage and then complete iteration gates;
6. update evidence only after the full gate is green;
7. never use skip, xfail or retry masking as completion evidence.

## 7. Iteration roadmap

| Iteration | Increment |
|---|---|
| I00 | Delivery governance, repository bootstrap and test gates |
| I01 | Shared contracts, plugin SDK and deterministic testkit |
| I02 | Six independent module shells and architecture enforcement |
| I03 | Collector core and deterministic acquisition |
| I04 | Runtime scheduling, execution and qualification |
| I05 | Incident authority, lifecycle, review and outbox |
| I06 | REST API and integration boundary |
| I07 | Accessible web/mobile client foundation |
| I08 | Compact composition and physical wildfire MVP |
| I09 | Structured analysis, claims, lineage and trust |
| I10 | Multimodal external evidence vertical slice |
| I11 | Flood hazard pack |
| I12 | Earthquake post-onset detection pack |
| I13 | Landslide pack |
| I14 | Official, scientific, publisher, platform and community sources |
| I15 | Plugin/pack lifecycle and isolated deployment |
| I16 | Offline operation, chaos and recovery |
| I17 | Security, privacy, accessibility and supply chain |
| I18 | Arm optimization, final benchmark and release candidate |

## 8. Detailed implementation plan
## I00 — Delivery governance, repository bootstrap and uncompromising test gates

**Increment:** A reproducible workspace where every later capability is tracked, every task modifies one primary file, and no iteration can pass by silently omitting tests.

**Entry condition:** The v0.13.0 modular documentation set is accepted as the architecture baseline.

### I00-S01 — Record architecture and delivery decisions

**Stage outcome:** The project has explicit decisions for modularity, atomic work, test gating and implementation profile.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I00-S01-T01` | `docs/adr/ADR-0001-modular-monolith-distributed-capable.md` | Record the six bounded contexts, compact-first deployment and transport-neutral ports. | ADR diagram and dependency rules match the v0.13.0 architecture. |
| `I00-S01-T02` | `docs/adr/ADR-0002-task-stage-iteration-workflow.md` | Define task, stage, iteration and one-primary-file remediation rules. | A validation example proves multi-file work is split into separate tasks. |
| `I00-S01-T03` | `docs/adr/ADR-0003-no-silent-test-skips.md` | Define active-capability testing and prohibit skip/xfail/flaky rerun as release evidence. | The ADR specifies failure handling and full-gate rerun. |
| `I00-S01-T04` | `docs/adr/ADR-0004-default-implementation-profile.md` | Select and pin the backend, persistence, transport, web, mobile, packaging and test toolchain. | The selected profile supports Linux Arm64, SQLite, generated contracts, PWA and mobile shell. |
| `I00-S01-T05` | `docs/architecture/source-baseline-v0.13.0.md` | Index the fourteen source specifications and manifest hashes. | Every uploaded document is represented exactly once. |

### I00-S02 — Create the workspace skeleton

**Stage outcome:** The repository layout exists without domain logic in shared or application roots.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I00-S02-T01` | `pyproject.toml` | Create workspace metadata, runtime constraints and development dependency groups. | Metadata parses and contains no module implementation dependency. |
| `I00-S02-T02` | `Makefile` | Add setup, quality, module, contract, integration, scenario, security, Arm and aggregate gate targets. | Every documented command resolves and unknown modules fail fast. |
| `I00-S02-T03` | `.gitignore` | Ignore environments, generated outputs, owned runtime stores, secrets and benchmark scratch data. | Required fixtures remain tracked. |
| `I00-S02-T04` | `.editorconfig` | Set line endings and indentation for Python, TypeScript, YAML, JSON, Markdown and shell. | EditorConfig validation finds no conflict. |
| `I00-S02-T05` | `README.md` | Add purpose, research warning, module index, setup and no-green-no-complete rule. | A new developer can identify the six modules and first commands. |
| `I00-S02-T06` | `docs/development/repository-map.md` | Document top-level directories and their authority constraints. | Each path has an owner or is explicitly non-domain infrastructure. |

### I00-S03 — Build capability and evidence tracking

**Stage outcome:** Tests cannot pass merely because a feature or suite is missing.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I00-S03-T01` | `provenance/capability-status.yaml` | Create planned, active, demonstrated and retired capability states with only I00 active. | Active capabilities without tests or evidence paths are rejected. |
| `I00-S03-T02` | `provenance/test-evidence.schema.json` | Define command, revision, environment, inputs, result, duration and artifact fields. | Positive and negative evidence fixtures validate. |
| `I00-S03-T03` | `scripts/validate_capability_status.py` | Fail when an active capability lacks owner, acceptance tests or evidence. | Deleting a test reference causes non-zero exit. |
| `I00-S03-T04` | `scripts/record_test_evidence.py` | Write immutable content-addressed evidence records. | Repeated runs never overwrite earlier evidence. |
| `I00-S03-T05` | `tests/governance/test_capability_registry.py` | Test legal state transitions and evidence freshness. | Direct planned-to-demonstrated transition fails. |

### I00-S04 — Establish continuous integration

**Stage outcome:** Every change runs fast checks and the main branch depends on the complete active gate.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I00-S04-T01` | `.github/workflows/ci-fast.yml` | Run format, lint, type, architecture and changed-scope tests on pull requests. | A deliberate lint failure blocks the job. |
| `I00-S04-T02` | `.github/workflows/ci-full.yml` | Run every active module, contract, integration, security and evidence lane. | Evidence uploads occur even when a lane fails. |
| `I00-S04-T03` | `.github/workflows/ci-arm.yml` | Create the Arm64 lane and mark it planned until hardware capabilities activate. | The job cannot report success as benchmark evidence before activation. |
| `I00-S04-T04` | `scripts/check_no_silent_skips.py` | Scan reports for unexpected skip, xfail, deselection, rerun and collection failure. | A synthetic skipped test fails the script. |
| `I00-S04-T05` | `tests/governance/test_ci_contract.py` | Assert required jobs, dependencies and artifacts exist. | Removing the aggregate dependency fails. |

### I00 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run `make setup`, format, lint, type, architecture, governance and aggregate gates.
- Inject one controlled failing test and prove the iteration remains incomplete.
- Inject one skipped test and prove the no-silent-skip checker fails.
- Repeat from a clean checkout to prove reproducibility.

**Mandatory evidence:**

- Validated ADR set
- Workspace dependency graph
- CI workflow validation
- Capability registry report
- Green aggregate gate record

**Completion rule:** `I00` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I01 — Shared contracts, plugin SDK and deterministic testkit

**Increment:** A tiny shared foundation of immutable contracts, lifecycle primitives, plugin governance and test utilities, with no hazard, trust, persistence, scheduling or UI business rules.

**Entry condition:** I00 is demonstrated and its complete gate remains green.

### I01-S01 — Create the contract catalog

**Stage outcome:** Cross-module messages have versioned schemas, examples, ownership and compatibility metadata.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I01-S01-T01` | `contracts/sentinel-contracts/pyproject.toml` | Create the independently versioned contract package. | It builds without module implementation imports. |
| `I01-S01-T02` | `contracts/sentinel-contracts/src/sentinel_contracts/envelope.py` | Define immutable CloudEvents-compatible envelope, correlation, causation, producer and idempotency. | Round-trip and malformed-envelope tests pass. |
| `I01-S01-T03` | `contracts/sentinel-contracts/src/sentinel_contracts/errors.py` | Define stable safe error/problem types. | Serialized errors contain no stack, secret or private payload. |
| `I01-S01-T04` | `contracts/sentinel-contracts/src/sentinel_contracts/artifacts.py` | Define content-addressed artifact references and privacy classes. | Inline binary payloads and invalid owner namespaces are rejected. |
| `I01-S01-T05` | `contracts/sentinel-contracts/catalog.yaml` | Register owners, consumers, semantic versions and current/N-1 ranges. | No active contract is ownerless or consumerless. |
| `I01-S01-T06` | `contracts/sentinel-contracts/tests/test_envelope.py` | Test identifiers, time, causation chains, delivery semantics and unknown fields. | Property tests cover valid and hostile values. |

### I01-S02 — Define module message schemas

**Stage outcome:** Every authoritative output and public command has a version-one schema and golden examples.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I01-S02-T01` | `contracts/sentinel-contracts/schemas/collector.v1.json` | Define observations, external items, source health and acquisition audit. | Units, clock quality, replay and policy metadata are required. |
| `I01-S02-T02` | `contracts/sentinel-contracts/schemas/analyzer.v1.json` | Define bundles, claims, media records, derivation and trust factors. | Immutable inputs, limitations and source spans/segments are required. |
| `I01-S02-T03` | `contracts/sentinel-contracts/schemas/runtime.v1.json` | Define jobs, results, hazard inference, lifecycle, health and benchmark samples. | Model/profile hashes, determinism and abstention are required. |
| `I01-S02-T04` | `contracts/sentinel-contracts/schemas/incident.v1.json` | Define incident inputs, commands, projections, transitions, reviews and effects. | Expected version and authoritative projection version are represented. |
| `I01-S02-T05` | `contracts/sentinel-contracts/schemas/api.v1.json` | Define public resources, pagination, cursors, audit context and errors. | Internal paths and queue addresses are structurally impossible. |
| `I01-S02-T06` | `contracts/sentinel-contracts/examples/golden-v1.yaml` | Add valid and invalid examples for every schema family. | Each schema has both acceptance and rejection fixtures. |

### I01-S03 — Implement plugin SDK governance

**Stage outcome:** Modules discover plugins but activate only pinned, verified, compatible and self-tested artifacts.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I01-S03-T01` | `sdk/sentinel-plugin-sdk/pyproject.toml` | Create the module-neutral plugin SDK. | Dependency scan finds no module implementation package. |
| `I01-S03-T02` | `sdk/sentinel-plugin-sdk/src/sentinel_plugin_sdk/manifest.py` | Parse identity, API, permissions, budgets, modes, contracts, fixtures and digests. | Impossible authority and unbounded resources are rejected. |
| `I01-S03-T03` | `sdk/sentinel-plugin-sdk/src/sentinel_plugin_sdk/lifecycle.py` | Implement discovery, verification, compatibility, self-test, activation, degradation and rollback. | State-machine property tests reject illegal transitions. |
| `I01-S03-T04` | `sdk/sentinel-plugin-sdk/src/sentinel_plugin_sdk/permissions.py` | Implement least-privilege network, filesystem, secret, artifact and model permissions. | Direct incident repository access is never grantable to plugins. |
| `I01-S03-T05` | `sdk/sentinel-plugin-sdk/tests/test_manifest_security.py` | Test digest, signature, permission, mode and circular dependency failures. | All malicious manifests fail with stable reason codes. |

### I01-S04 — Create deterministic testkit

**Stage outcome:** All modules share virtual time, fake ports, fault injection and signed scenarios.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I01-S04-T01` | `sdk/sentinel-testkit/pyproject.toml` | Create the test-only package boundary. | Production runtime packages do not depend on it. |
| `I01-S04-T02` | `sdk/sentinel-testkit/src/sentinel_testkit/virtual_clock.py` | Implement deterministic wall, monotonic and event time. | Timeout and ordering tests repeat identically. |
| `I01-S04-T03` | `sdk/sentinel-testkit/src/sentinel_testkit/fake_ports.py` | Provide bounded fake command, event, job, artifact and projection ports. | Fakes model timeout, duplicate, reorder, corruption and outage. |
| `I01-S04-T04` | `sdk/sentinel-testkit/src/sentinel_testkit/scenario.py` | Define signed scenario, time map, invariants, transcript and reset. | A minimal scenario replays with the same semantic hash. |
| `I01-S04-T05` | `sdk/sentinel-testkit/tests/test_determinism.py` | Test clock, seed, transcript and reset determinism. | Two clean runs match. |

### I01-S05 — Generate and verify bindings

**Stage outcome:** Backend and clients use bindings generated from one contract catalog.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I01-S05-T01` | `scripts/generate_contracts.py` | Generate Python, TypeScript, AsyncAPI and OpenAPI fragments. | Clean regeneration produces no diff. |
| `I01-S05-T02` | `contracts/compatibility-matrix/current-n-1.yaml` | Declare additive compatibility and prohibited semantic changes. | Unit, identity and requiredness mutations fail. |
| `I01-S05-T03` | `tests/contracts/test_schema_examples.py` | Validate every example and catalog reference. | Failures identify exact schema and path. |
| `I01-S05-T04` | `tests/contracts/test_generated_bindings.py` | Compile and round-trip Python and TypeScript models. | Canonical semantics survive both bindings. |
| `I01-S05-T05` | `tests/contracts/test_compatibility.py` | Enforce major-version rules for breaking changes. | Breaking-change mutations are detected. |

### I01 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all I00 gates plus package builds, schema/example validation, generated-binding compilation, compatibility mutations and plugin state-machine tests.
- Prove shared packages contain no module-specific domain or repository implementation.
- Regenerate bindings twice from clean inputs and compare hashes.
- Reject malicious plugin manifests and oversized inline artifacts.

**Mandatory evidence:**

- Contract catalog and compatibility report
- Generated binding hashes
- Plugin SDK conformance report
- Determinism transcript
- Green full regression gate

**Completion rule:** `I01` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I02 — Six independent module shells and enforced ownership boundaries

**Increment:** All six modules start alone with fake ports, own configuration/state namespaces, expose lifecycle diagnostics and fail architecture tests on forbidden coupling.

**Entry condition:** I01 is demonstrated and generated contracts are stable enough for scaffolding.

### I02-S01 — Create backend module packages

**Stage outcome:** Modules 01–05 are separate packages with isolated dependencies.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I02-S01-T01` | `modules/streaming-source-collector/pyproject.toml` | Create Module 01 metadata and contract range. | Build contains no dependency on modules 02–06. |
| `I02-S01-T02` | `modules/analysis-enrichment-engine/pyproject.toml` | Create Module 02 metadata and contract range. | Build contains no business-module dependency. |
| `I02-S01-T03` | `modules/model-workload-runtime/pyproject.toml` | Create Module 03 metadata and contract range. | Build contains no business-module dependency. |
| `I02-S01-T04` | `modules/incident-event-engine/pyproject.toml` | Create Module 04 metadata and exclusive incident authority declaration. | No other package declares incident authority. |
| `I02-S01-T05` | `modules/rest-api-integration-gateway/pyproject.toml` | Create Module 05 metadata and contract range. | No incident repository dependency exists. |

### I02-S02 — Create client workspace

**Stage outcome:** Web, mobile and shared-domain packages build independently from generated contracts.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I02-S02-T01` | `modules/client-applications/package.json` | Create the client workspace and canonical scripts. | Locked installation succeeds. |
| `I02-S02-T02` | `modules/client-applications/shared-domain/package.json` | Create framework-neutral shared domain package. | No browser/native UI dependency exists. |
| `I02-S02-T03` | `modules/client-applications/web/package.json` | Create web/PWA shell package. | Minimal production build succeeds. |
| `I02-S02-T04` | `modules/client-applications/mobile-shell/package.json` | Create mobile shell package. | Minimal type/build check succeeds. |
| `I02-S02-T05` | `modules/client-applications/shared-domain/src/index.ts` | Export generated types and empty ports only. | No API server, DB or filesystem implementation is imported. |

### I02-S03 — Implement common module lifecycle

**Stage outcome:** Each backend module validates configuration, starts, reports readiness/health, drains, stops and produces diagnostics.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I02-S03-T01` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/bootstrap/runtime.py` | Implement Module 01 lifecycle with fake ports. | Ready, degraded, drain and stop transcript passes. |
| `I02-S03-T02` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/bootstrap/runtime.py` | Implement Module 02 lifecycle with fake ports. | Dependency loss and recovery pass. |
| `I02-S03-T03` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/bootstrap/runtime.py` | Implement Module 03 lifecycle with fake registry/worker/probe. | No workload executes before qualification readiness. |
| `I02-S03-T04` | `modules/incident-event-engine/src/sentinel_incident_event_engine/bootstrap/runtime.py` | Implement Module 04 recovery-before-ready lifecycle. | Fresh escalation is withheld before reconciliation. |
| `I02-S03-T05` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/bootstrap/runtime.py` | Implement Module 05 lifecycle with fake incident client. | Readiness distinguishes startup from upstream degradation. |

### I02-S04 — Create standalone runners and harnesses

**Stage outcome:** Every module is testable without the full solution.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I02-S04-T01` | `apps/sentinel-module-runner/pyproject.toml` | Create the standalone runner package. | It imports public bootstrap packages only. |
| `I02-S04-T02` | `apps/sentinel-module-runner/src/sentinel_module_runner/main.py` | Implement start, readiness, diagnostics, drain and stop. | All backend modules follow the same black-box lifecycle. |
| `I02-S04-T03` | `modules/client-applications/web/src/test-harness.ts` | Create deterministic browser harness with generated mocks. | Web shell starts without live server. |
| `I02-S04-T04` | `modules/client-applications/mobile-shell/src/test-harness.ts` | Create deterministic mobile harness with fake device services. | Mobile shell starts without device APIs. |
| `I02-S04-T05` | `tests/component/test_all_module_lifecycles.py` | Run backend modules only through public runner interfaces. | Normal, malformed config, timeout, drain and restart pass. |

### I02-S05 — Enforce architecture boundaries

**Stage outcome:** Forbidden imports, stores, authority and namespaces fail before functional tests.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I02-S05-T01` | `architecture/import-rules.toml` | Declare allowed shared dependencies and prohibit business-module imports. | Synthetic cross-module import is detected. |
| `I02-S05-T02` | `architecture/owned-namespaces.yaml` | Declare databases, artifacts, secrets and authority owner. | Duplicate owners and undeclared paths fail. |
| `I02-S05-T03` | `scripts/check_architecture_boundaries.py` | Scan imports, metadata, SQL/path strings, permissions and cycles. | Each forbidden-coupling fixture fails specifically. |
| `I02-S05-T04` | `tests/architecture/test_authority_boundaries.py` | Test connector-only, runtime-only, incident-only and API-only authorities. | Moving an adapter to the wrong module fails. |
| `I02-S05-T05` | `tests/architecture/test_client_boundaries.ts` | Prohibit server DB/filesystem/internal transport and duplicated policy in clients. | Known forbidden imports are rejected. |

### I02 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior tests plus six package builds, backend lifecycle components, client shell builds, architecture mutations and owned-state migration smoke tests.
- Start every module alone from a clean temporary directory and exercise degraded/restart behavior.
- Attempt a forbidden import, cross-database path and impossible plugin permission; each must fail.
- Run `make test-all-modules` and the complete repository gate.

**Mandatory evidence:**

- Six package artifacts
- Standalone lifecycle transcripts
- Architecture graph
- Owned namespace report
- Green full regression gate

**Completion rule:** `I02` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I03 — Streaming Source Collector core and deterministic acquisition

**Increment:** Module 01 acquires physical, structured and fixture inputs through policy gates, preserves timing/quality/provenance, quarantines hostile media and emits bounded idempotent outputs without deciding incident truth.

**Entry condition:** I02 is demonstrated and Module 01 standalone lifecycle is green.

### I03-S01 — Implement collector domain primitives

**Stage outcome:** Pure rules cover observation quality, time, units, sequence, freshness and replay.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I03-S01-T01` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/domain/observation.py` | Implement canonical observation validation and missingness. | Invalid units, times and quality states fail property tests. |
| `I03-S01-T02` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/domain/time_quality.py` | Implement capture/sample/ingest time, boot ID, clock quality and watermarks. | Late, reordered and replayed items are labeled deterministically. |
| `I03-S01-T03` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/domain/deduplication.py` | Implement source identity, duplicate, replay and replace-latest decisions. | Redelivery yields the same canonical identity. |
| `I03-S01-T04` | `modules/streaming-source-collector/tests/property/test_observation_properties.py` | Generate timestamps, gaps, units, missingness and duplicates. | Shrinking finds minimal counterexamples. |

### I03-S02 — Implement acquisition policy and quarantine

**Stage outcome:** No byte is fetched or ordinarily persisted before rights, privacy and resource policy succeeds.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I03-S02-T01` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/application/acquisition_policy.py` | Implement entitlement, permitted use, retention and analysis authorization. | Expired or forbidden sources stop before retrieval. |
| `I03-S02-T02` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/adapters/quarantine_file.py` | Implement bounded content-addressed hostile-byte storage. | Byte, age, disk and retention limits hold under concurrency. |
| `I03-S02-T03` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/application/privacy_minimization.py` | Minimize coordinates and metadata before ordinary persistence. | Restricted fields never appear in logs or ordinary store. |
| `I03-S02-T04` | `modules/streaming-source-collector/tests/nonfunctional/test_parser_and_quarantine_budgets.py` | Fuzz structured/media headers and resource limits. | No item causes unbounded memory, disk or time. |

### I03-S03 — Implement owned ingress state and bounded pipeline

**Stage outcome:** Cursor commit, ledger and output handoff are crash-safe and at-least-once aware.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I03-S03-T01` | `modules/streaming-source-collector/migrations/0001_ingress_ledger.sql` | Create source, cursor, idempotency, audit and health tables. | Empty and N-1 migration tests pass. |
| `I03-S03-T02` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/adapters/sqlite_repository.py` | Implement cursor, ledger, deduplication and audit persistence. | Crash around commit causes safe redelivery, not loss. |
| `I03-S03-T03` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/application/pipeline.py` | Implement bounded connector→policy→decode→normalize→privacy→ledger→emit flow. | Queue capacity, age and drop/coalesce policy are observable. |
| `I03-S03-T04` | `modules/streaming-source-collector/src/sentinel_streaming_source_collector/diagnostics/metrics.py` | Expose validation, latency, queue, retry, duplicate, plugin and store metrics. | Telemetry excludes private raw payloads. |
| `I03-S03-T05` | `modules/streaming-source-collector/tests/component/test_crash_redelivery.py` | Test failure at every ledger/cursor/handoff boundary. | Each item is durable or safely redelivered. |

### I03-S04 — Add reference connectors and fixtures

**Stage outcome:** Physical, structured, upload and signed scenario workflows pass the same plugin contract.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I03-S04-T01` | `plugins/collector-fixture-source/src/sentinel_fixture_source/plugin.py` | Implement signed deterministic scenario replay. | Two runs produce identical envelopes. |
| `I03-S04-T02` | `plugins/collector-physical-emulator/src/sentinel_physical_emulator/plugin.py` | Implement camera, IMU and environmental emulator with faults. | Gaps, reboot and clock degradation are visible. |
| `I03-S04-T03` | `plugins/collector-structured-file/src/sentinel_structured_file/plugin.py` | Implement bounded JSON/CSV fixture connector. | Malformed remote records do not block physical capture. |
| `I03-S04-T04` | `plugins/collector-local-upload/src/sentinel_local_upload/plugin.py` | Implement consented upload metadata and quarantine handoff. | Rights and privacy metadata are mandatory. |
| `I03-S04-T05` | `modules/streaming-source-collector/fixtures/conformance.yaml` | Add success, timeout, malformed, rate-limit, entitlement, replay and overload cases. | Every selected connector passes. |
| `I03-S04-T06` | `modules/streaming-source-collector/tests/plugin_conformance/test_collector_plugins.py` | Run lifecycle, permission and budget conformance. | A deliberately invalid plugin is rejected. |

### I03-S05 — Publish collector contracts

**Stage outcome:** Analyzer, Runtime and Incident consumers verify the real packaged Collector.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I03-S05-T01` | `modules/streaming-source-collector/contracts/asyncapi.yaml` | Document observation, external item, health and audit channels. | AsyncAPI and delivery checks pass. |
| `I03-S05-T02` | `modules/streaming-source-collector/contracts/provider-kit.yaml` | Publish consumer cases for Modules 02, 03 and 04. | Cases execute against the package. |
| `I03-S05-T03` | `modules/streaming-source-collector/tests/contract/test_collector_contracts.py` | Test schemas, examples and N-1 expectations. | Unit/identity breaking mutations fail. |
| `I03-S05-T04` | `modules/streaming-source-collector/README.md` | Document live/offline modes, policy, queues, state and commands. | Runbook commands execute. |

### I03 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior gates plus collector unit/property, parser fuzz, plugin conformance, migrations, contracts, component and crash-redelivery tests.
- Stress physical and remote inputs together; malformed remote input must not block the physical path.
- Prove no Collector output can declare or mutate incident truth.
- Record queue, age and RSS behavior during overload.

**Mandatory evidence:**

- Collector package/SBOM fragment
- Connector conformance report
- Fuzz/resource report
- Crash-redelivery transcript
- Provider kit verification
- Green full regression gate

**Completion rule:** `I03` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I04 — Model & Workload Runtime core, scheduling and qualification

**Increment:** Module 03 accepts only validated jobs and signed profiles, schedules them under criticality/deadline/resource rules, executes isolated workers and emits traceable results, fallbacks or abstentions.

**Entry condition:** I03 is demonstrated and Collector job contracts are available.

### I04-S01 — Implement registry and qualification

**Stage outcome:** Only pinned, digest-verified and qualified workloads execute in release modes.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I04-S01-T01` | `modules/model-workload-runtime/migrations/0001_runtime_registry.sql` | Create registry, qualification, job, telemetry and idempotency tables. | Current and N-1 migrations pass. |
| `I04-S01-T02` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/domain/workload_manifest.py` | Define workload identity, hashes, constraints, quality gates, fallback and determinism. | Arbitrary upload/URL and missing digest fail. |
| `I04-S01-T03` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/application/qualification.py` | Implement known-answer, malformed-model, quality, latency/RSS, interference and rollback qualification. | Workload cannot activate before all required evidence. |
| `I04-S01-T04` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/adapters/sqlite_registry.py` | Implement read-only release registry and qualification persistence. | Judge/benchmark mutation is refused. |
| `I04-S01-T05` | `modules/model-workload-runtime/tests/test_qualification.py` | Test activation, invalidation and rollback. | Changing model/provider/config invalidates evidence. |

### I04-S02 — Implement admission and scheduling

**Stage outcome:** Tier A reserve and deadline-aware scheduling shed lower work before false guarantees.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I04-S02-T01` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/domain/scheduling.py` | Implement fixed criticality, EDF within tier, aging, reserve and pressure gates. | Virtual-clock ordering and starvation invariants pass. |
| `I04-S02-T02` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/application/admission.py` | Return accept, defer, validated fallback or reject with reasons. | Every decision records slack and resource consequence. |
| `I04-S02-T03` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/application/residency.py` | Implement warm/cold budgets and residency hysteresis. | Pressure tests avoid thrashing. |
| `I04-S02-T04` | `modules/model-workload-runtime/tests/property/test_scheduler_state_machine.py` | Generate arrivals, deadlines, cancellations, retries and pressure. | Capacity, reserve, fairness and terminal states hold. |

### I04-S03 — Implement isolated execution and probes

**Stage outcome:** Jobs run with bounded input, worker and telemetry controls.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I04-S03-T01` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/adapters/process_worker.py` | Implement isolated worker with wall, RSS and I/O limits. | Hung/crashing/oversized jobs terminate safely. |
| `I04-S03-T02` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/adapters/linux_resource_probe.py` | Read CPU, memory, thermal and optional power pressure. | Unavailable sensors degrade explicitly. |
| `I04-S03-T03` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/application/execution.py` | Implement prepare→dispatch→collect→calibrate→emit. | Cancellation points are explicit; native kernels are not falsely preemptible. |
| `I04-S03-T04` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/diagnostics/metrics.py` | Expose admission, queue, execution, fallback, abstention and pressure metrics. | Telemetry overhead remains bounded. |
| `I04-S03-T05` | `modules/model-workload-runtime/tests/component/test_worker_failures.py` | Test timeout, crash, malformed output, resource excess and restart. | No job remains stuck RUNNING. |

### I04-S04 — Add reference workload plugins

**Stage outcome:** Scheduling and result contracts are demonstrated before final hazard workloads.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I04-S04-T01` | `plugins/runtime-deterministic-threshold/src/sentinel_threshold_workload/plugin.py` | Implement deterministic threshold workload. | Known answers are bitwise stable. |
| `I04-S04-T02` | `plugins/runtime-reference-classifier/src/sentinel_reference_classifier/plugin.py` | Implement compact fixture classifier. | Quality and malformed-model tests pass on Arm64. |
| `I04-S04-T03` | `plugins/runtime-reference-backend/src/sentinel_reference_backend/plugin.py` | Implement one bounded inference backend. | External model/data fetch is rejected. |
| `I04-S04-T04` | `modules/model-workload-runtime/fixtures/conformance.yaml` | Add known-answer, invalid model, overload, fallback and abstention cases. | All selected plugins pass. |

### I04-S05 — Publish runtime contracts and benchmark harness

**Stage outcome:** Collectors, Analyzer and Incident verify jobs/results and benchmarks are quality-first.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I04-S05-T01` | `modules/model-workload-runtime/contracts/asyncapi.yaml` | Document jobs, results, inference, lifecycle and health. | Schema/delivery checks pass. |
| `I04-S05-T02` | `modules/model-workload-runtime/contracts/provider-kit.yaml` | Publish normal, cancellation, fallback and incompatible cases. | Consumers execute them against the package. |
| `I04-S05-T03` | `modules/model-workload-runtime/src/sentinel_model_workload_runtime/application/benchmark.py` | Implement opportunity-equivalent B0/B1/O1 sampling. | Runs fail when quality or host-noise gates fail. |
| `I04-S05-T04` | `modules/model-workload-runtime/tests/nonfunctional/test_interference.py` | Measure Tier A under CPU/RSS background pressure. | Reserve holds or overload is declared honestly. |
| `I04-S05-T05` | `modules/model-workload-runtime/README.md` | Document qualification, scheduling, fallback and benchmark scope. | No universal performance claim is made. |

### I04 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all previous gates plus scheduler/property, worker fault, plugin conformance, known-answer quality, migration, contract and Arm smoke tests.
- Create background pressure and verify Tier A admission, fallback or explicit overload.
- Attempt arbitrary model upload and unqualified execution; both must fail.
- Run B0/B1/O1 with identical opportunities and evidence hashes.

**Mandatory evidence:**

- Qualification report
- Scheduler invariant report
- Known-answer/quality evidence
- Interference/RSS report
- Benchmark sample bundle
- Green full regression gate

**Completion rule:** `I04` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I05 — Incident & Event Engine authority and generic lifecycle

**Increment:** Module 04 becomes the sole incident writer with idempotent inbox, append-only journal, deterministic projections, evidence graph, review workflow, transactional outbox and restart reconciliation.

**Entry condition:** I04 is demonstrated and inference/analysis contracts are stable.

### I05-S01 — Implement journal and projections

**Stage outcome:** Incident state is reproducible from an append-only owned store.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I05-S01-T01` | `modules/incident-event-engine/migrations/0001_incident_journal.sql` | Create inbox, journal, snapshot, projection, review and outbox tables. | Migration and rollback rehearsal pass. |
| `I05-S01-T02` | `modules/incident-event-engine/src/sentinel_incident_event_engine/domain/events.py` | Define immutable incident, evidence-link, review and lifecycle events. | Events include inputs, reasons and artifact references. |
| `I05-S01-T03` | `modules/incident-event-engine/src/sentinel_incident_event_engine/adapters/sqlite_repository.py` | Append events, update projection and insert outbox atomically with expected version. | Crash points cannot produce orphan projection/effect. |
| `I05-S01-T04` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/rebuild.py` | Rebuild snapshots and projections from journal. | Rebuild hash equals live semantic hash. |
| `I05-S01-T05` | `modules/incident-event-engine/tests/component/test_event_store_recovery.py` | Test corruption, snapshot fallback, inbox replay and outbox reconciliation. | Module remains non-ready until reconciliation. |

### I05-S02 — Implement lifecycle commands

**Stage outcome:** Create, update, link, merge, split, resolve and reopen obey optimistic concurrency.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I05-S02-T01` | `modules/incident-event-engine/src/sentinel_incident_event_engine/domain/incident.py` | Define incident identity, status, severity, location, coverage, trust and version. | Invalid terminal/version transitions fail. |
| `I05-S02-T02` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/commands.py` | Implement idempotent command handling with expected version. | Duplicate returns same outcome; stale version conflicts. |
| `I05-S02-T03` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/matching.py` | Apply matcher proposals without allowing plugin commits. | Ambiguous proposals remain auditable/reviewable. |
| `I05-S02-T04` | `modules/incident-event-engine/tests/property/test_incident_state_machine.py` | Generate lifecycle operation sequences. | State, version, causation and journal invariants hold. |

### I05-S03 — Implement evidence graph and coverage

**Stage outcome:** Support, contradiction, derivation and independence cannot bypass authority rules.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I05-S03-T01` | `modules/incident-event-engine/src/sentinel_incident_event_engine/domain/evidence_graph.py` | Represent claims, families, derivation, support and contradiction. | Cycles and duplicate-family false corroboration fail. |
| `I05-S03-T02` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/corroboration.py` | Evaluate independence and trust dimensions without collapsing them. | External low-trust evidence cannot verify/resolve/safe. |
| `I05-S03-T03` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/coverage.py` | Implement coverage-gated negative evidence. | Missing data never becomes normal or safe. |
| `I05-S03-T04` | `modules/incident-event-engine/tests/test_authority_invariants.py` | Test no truth bypass and coverage rules. | Mutating each invariant is detected. |

### I05-S04 — Implement review, alert budgets and effects

**Stage outcome:** Human decisions and side effects are durable and reconstructable.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I05-S04-T01` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/review.py` | Implement acknowledgement, review, snooze, expiry and resolution constraints. | Unauthorized/stale review fails. |
| `I05-S04-T02` | `modules/incident-event-engine/src/sentinel_incident_event_engine/domain/alert_budget.py` | Implement incident/site/channel alert budgets. | Repeated evidence does not storm alerts. |
| `I05-S04-T03` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/outbox_dispatch.py` | Dispatch effects idempotently without changing history. | Retries preserve one semantic effect. |
| `I05-S04-T04` | `modules/incident-event-engine/src/sentinel_incident_event_engine/application/after_event_review.py` | Generate AER from journal, delays, failures and recovery. | AER reconciles with authoritative events. |
| `I05-S04-T05` | `modules/incident-event-engine/tests/component/test_outbox_and_review.py` | Test crash/retry, snooze, budgets and AER. | No effect occurs without outbox intent. |

### I05-S05 — Add generic policy SDK and contracts

**Stage outcome:** Hazard packs define vocabulary and state rules without repository authority.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I05-S05-T01` | `modules/incident-event-engine/src/sentinel_incident_event_engine/plugins/hazard_policy.py` | Define narrow HazardPolicyPack context and proposals. | Plugin receives immutable inputs only. |
| `I05-S05-T02` | `plugins/incident-generic-hazard/src/sentinel_generic_hazard/plugin.py` | Implement reference candidate→observed→reviewed→resolved policy. | Table-driven transitions pass. |
| `I05-S05-T03` | `modules/incident-event-engine/contracts/asyncapi.yaml` | Document inputs, commands, transitions, projections, reviews and effects. | Provider/consumer checks pass. |
| `I05-S05-T04` | `modules/incident-event-engine/contracts/provider-kit.yaml` | Publish cases for Modules 01–03 and 05. | Duplicate, stale and restart cases execute. |
| `I05-S05-T05` | `modules/incident-event-engine/README.md` | Document sole authority, event sourcing, coverage, review and recovery. | No alternate write path is documented. |

### I05 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior gates plus migration/rebuild, lifecycle state machine, authority invariants, policy conformance, inbox/outbox crash, review and AER tests.
- Replay the same input/command transcript after rebuild and compare semantic projections.
- Attempt direct incident writes from every other module; all must fail.
- Run current/N-1 provider/consumer verification.

**Mandatory evidence:**

- Journal/rebuild proof
- Authority invariant report
- Policy conformance
- Outbox crash transcript
- AER reconciliation
- Green full regression gate

**Completion rule:** `I05` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I06 — REST API & Integration Gateway public boundary

**Increment:** Module 05 provides the only supported client/integration boundary with versioned REST resources, idempotent commands, optimistic concurrency, privacy filtering, resumable projections and stable errors.

**Entry condition:** I05 is demonstrated and Incident provider contracts are executable.

### I06-S01 — Implement projection reads

**Stage outcome:** The API consumes authoritative projections without reading incident tables.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I06-S01-T01` | `modules/rest-api-integration-gateway/migrations/0001_api_state.sql` | Create sessions, rate limits, cursors and audit context only. | No incident table exists. |
| `I06-S01-T02` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/application/projections.py` | Consume/version projections and trigger resync on gaps. | The API never invents missing state. |
| `I06-S01-T03` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/adapters/sqlite_state.py` | Persist only API-owned state. | Incident-domain joins/columns fail architecture checks. |
| `I06-S01-T04` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/http/resources.py` | Implement incident, timeline, evidence and health reads. | ETag, pagination, filters and projection age are present. |
| `I06-S01-T05` | `modules/rest-api-integration-gateway/tests/component/test_read_resources.py` | Test empty, stale, rebuilding and privacy-filtered states. | REST responses remain deterministic. |

### I06-S02 — Implement command boundary

**Stage outcome:** Mutations become validated idempotent IncidentCommands with expected versions.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I06-S02-T01` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/http/commands.py` | Validate schema, idempotency and expected version. | Malformed, duplicate and stale commands have stable outcomes. |
| `I06-S02-T02` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/application/idempotency.py` | Persist key, canonical payload hash and result linkage. | Same key with different payload fails. |
| `I06-S02-T03` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/http/problem_details.py` | Map safe errors to Problem Details reason codes. | No internal stack/path/secret leaks. |
| `I06-S02-T04` | `modules/rest-api-integration-gateway/tests/component/test_commands.py` | Test accepted, duplicate, conflict, forbidden and upstream-degraded commands. | Behavior matches Incident provider kit. |

### I06-S03 — Implement authorization and privacy

**Stage outcome:** Roles and purpose control actions and field precision.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I06-S03-T01` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/application/identity.py` | Define operator, reviewer, administrator and integration identities. | Anonymous access is explicitly limited. |
| `I06-S03-T02` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/application/authorization.py` | Implement deny-by-default action and field matrix. | Every active route/field combination is covered. |
| `I06-S03-T03` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/application/privacy_filter.py` | Filter exact coordinates, raw media and private source identity. | Role snapshots prove minimization. |
| `I06-S03-T04` | `modules/rest-api-integration-gateway/tests/security/test_authorization_matrix.py` | Generate role×route×action×field tests. | No uncovered active combination remains. |

### I06-S04 — Implement resumable projections and export

**Stage outcome:** Clients resume streams, detect gaps and request authorized immutable exports.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I06-S04-T01` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/http/sse.py` | Implement authenticated replay, heartbeat, cursor resume and bounds. | Gap/expired cursor forces REST resync. |
| `I06-S04-T02` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/http/websocket.py` | Implement optional WebSocket transport behind same port. | Semantics match SSE transcripts. |
| `I06-S04-T03` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/application/export.py` | Build authorized derived export manifests. | Parent hashes remain and denied fields disappear. |
| `I06-S04-T04` | `modules/rest-api-integration-gateway/tests/component/test_projection_resume.py` | Test replay, gap, overflow, heartbeat and resync. | Irreplaceable transitions are never stream-only. |

### I06-S05 — Publish OpenAPI and clients

**Stage outcome:** Web, mobile and integrations compile from one authoritative API document.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I06-S05-T01` | `modules/rest-api-integration-gateway/contracts/openapi.yaml` | Publish OpenAPI 3.1.2 resources, commands, errors, auth and pagination. | Lint/schema validation passes. |
| `I06-S05-T02` | `scripts/generate_api_clients.py` | Generate Python/TypeScript clients. | Clean regeneration has no drift. |
| `I06-S05-T03` | `modules/rest-api-integration-gateway/contracts/provider-kit.yaml` | Publish auth, privacy, idempotency, conflict and resume cases. | Clients execute cases against packaged API. |
| `I06-S05-T04` | `modules/rest-api-integration-gateway/tests/contract/test_openapi_clients.py` | Compile N and N-1 clients and run provider cases. | Supported versions pass. |
| `I06-S05-T05` | `modules/rest-api-integration-gateway/README.md` | Document public boundary, versioning, streaming and resync. | No internal transport/database is public. |

### I06 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior gates plus OpenAPI lint, generated clients, API black-box, authorization/privacy, idempotency/concurrency, pagination, resume and Incident↔API pairwise tests.
- Prove the API cannot write incident tables or synthesize projections from raw tables.
- Run N and N-1 generated clients against the package.
- Overflow the projection stream and verify safe REST resync.

**Mandatory evidence:**

- OpenAPI/client hashes
- Authorization/privacy matrix
- Idempotency/conflict transcript
- Projection-resume report
- Incident↔API verification
- Green full regression gate

**Completion rule:** `I06` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I07 — Accessible web/mobile client foundation and operator workflow

**Increment:** Module 06 provides shared semantics, responsive web/PWA and mobile shells, mission control, incident/evidence review, offline command state and visible degradation without duplicating server truth logic.

**Entry condition:** I06 is demonstrated and generated API clients are stable.

### I07-S01 — Implement shared client domain

**Stage outcome:** Web and mobile use identical terminology, trust/coverage display and command state.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I07-S01-T01` | `modules/client-applications/shared-domain/src/models.ts` | Re-export generated API models and define client-only state. | No duplicate server-domain schema exists. |
| `I07-S01-T02` | `modules/client-applications/shared-domain/src/terminology.ts` | Define incident, hazard, trust, source-mode, coverage and safety wording. | Tests reject false-safe and earthquake-prediction wording. |
| `I07-S01-T03` | `modules/client-applications/shared-domain/src/trust-presentation.ts` | Present standing, integrity, freshness, extraction, independence and corroboration separately. | No opaque single trust badge replaces dimensions. |
| `I07-S01-T04` | `modules/client-applications/shared-domain/src/connection-state.ts` | Define online, reconnecting, offline, stale, resync and conflict states. | State-machine tests cover transitions. |
| `I07-S01-T05` | `modules/client-applications/shared-domain/tests/domain.test.ts` | Run shared semantic tests in both shells. | Web/mobile execute the same cases. |

### I07-S02 — Build mission-control web/PWA

**Stage outcome:** Operators see incidents, coverage, source health and system health independently.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I07-S02-T01` | `modules/client-applications/web/src/app.tsx` | Create responsive shell, routing, error boundary and connection banner. | Keyboard navigation reaches primary routes. |
| `I07-S02-T02` | `modules/client-applications/web/src/features/mission-control.tsx` | Render incident summary, hazard filters, coverage and degradation. | Cached data always shows age/source mode. |
| `I07-S02-T03` | `modules/client-applications/web/src/features/incident-detail.tsx` | Render timeline, evidence, reasons, review and authoritative version. | No color-only severity or hidden blocker. |
| `I07-S02-T04` | `modules/client-applications/web/src/services/api.ts` | Use only generated REST/projection clients. | No hand-written incident request type or internal URL. |
| `I07-S02-T05` | `modules/client-applications/web/tests/mission-control.test.tsx` | Test empty, normal, degraded, stale, gap and conflict transcripts. | Accessible names and data age are asserted. |

### I07-S03 — Build mobile shell and device ports

**Stage outcome:** Field users get the same semantics behind narrow device interfaces.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I07-S03-T01` | `modules/client-applications/mobile-shell/src/app.tsx` | Create navigation, connection state and shared-domain integration. | Works with fake device services. |
| `I07-S03-T02` | `modules/client-applications/mobile-shell/src/ports/device-capability.ts` | Define capture, notification and share ports. | No platform code leaks into shared domain. |
| `I07-S03-T03` | `modules/client-applications/mobile-shell/src/features/incident-detail.tsx` | Render mobile incident/evidence/review workflow. | Status/version match web transcript. |
| `I07-S03-T04` | `modules/client-applications/mobile-shell/tests/shell.test.tsx` | Test navigation, offline, conflict and notification fixtures. | No permission is requested before user action. |

### I07-S04 — Implement offline cache and command queue

**Stage outcome:** Read state remains age-labeled offline and commands retry idempotently with visible conflicts.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I07-S04-T01` | `modules/client-applications/shared-domain/src/offline-command.ts` | Implement queued, submitting, accepted, duplicate, conflict, expired and failed states. | Property tests prove terminal/retry invariants. |
| `I07-S04-T02` | `modules/client-applications/web/src/services/offline-store.ts` | Implement protected bounded web cache and queue. | Private data is not stored in plaintext where preventable. |
| `I07-S04-T03` | `modules/client-applications/mobile-shell/src/services/offline-store.ts` | Implement secure mobile cache and queue. | Queue survives restart with idempotency/version. |
| `I07-S04-T04` | `modules/client-applications/shared-domain/tests/offline-command.property.test.ts` | Generate reconnect, duplicate, conflict, expiry and retry sequences. | No duplicate semantic action occurs. |

### I07-S05 — Establish accessibility and API contracts

**Stage outcome:** Accessibility starts immediately and Module 05↔06 contracts are executable.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I07-S05-T01` | `modules/client-applications/web/tests/accessibility.test.tsx` | Automate accessibility checks for mission control and detail. | No serious/critical violations. |
| `I07-S05-T02` | `modules/client-applications/mobile-shell/tests/accessibility.test.tsx` | Test labels, focus and text scaling. | Primary workflow remains usable. |
| `I07-S05-T03` | `integration-tests/pairwise/api-clients/contract.spec.ts` | Run generated client, authorization, resume and offline cases against real API. | Web/mobile expectations pass. |
| `I07-S05-T04` | `modules/client-applications/README.md` | Document boundaries, offline behavior, accessibility and harnesses. | Clean build/test commands work. |

### I07 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior gates plus web/mobile builds, shared semantics, API consumer contracts, UI transcripts, offline state machine and automated accessibility.
- Compare web/mobile rendering for the same projection transcript.
- Disconnect during a command, restart, reconnect and verify duplicate/conflict handling.
- Capture keyboard-only and basic screen-reader evidence.

**Mandatory evidence:**

- Web/PWA build
- Mobile-shell build
- Semantic parity report
- Offline transcript
- Accessibility evidence
- API↔Clients verification
- Green full regression gate

**Completion rule:** `I07` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I08 — Compact composition root and first physical wildfire vertical slice

**Increment:** A complete sensor/fixture→Collector→Runtime→Incident→API→Web/Mobile flow creates a conservative wildfire candidate, supports operator review and remains traceable. This is the first evaluator-usable MVP.

**Entry condition:** I03–I07 are demonstrated and all physical-path pairwise contracts are green.

### I08-S01 — Build compact integration fabric

**Stage outcome:** Modules compose through bounded in-memory ports while retaining separate stores/contracts.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I08-S01-T01` | `apps/sentinel-node/pyproject.toml` | Create composition-root package using public bootstraps only. | No module internal import exists. |
| `I08-S01-T02` | `apps/sentinel-node/src/sentinel_node/channels.py` | Implement bounded command, event, projection and job channels. | Overflow/coalescing/poison behavior is tested. |
| `I08-S01-T03` | `apps/sentinel-node/src/sentinel_node/composition.py` | Wire Module 01→03→04→05 through public ports. | No hazard/trust/incident rule exists here. |
| `I08-S01-T04` | `apps/sentinel-node/src/sentinel_node/health.py` | Expose read-only aggregate health. | Module-specific reasons remain intact. |
| `I08-S01-T05` | `integration-tests/pairwise/collector-runtime/test_hot_path.py` | Verify Observation→Job→Result identity, age and faults. | Causation and capture age are preserved. |

### I08-S02 — Implement wildfire hazard pack v1

**Stage outcome:** Wildfire uses low-cost screening, bounded confirmation, temporal persistence and camera-health coverage.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I08-S02-T01` | `plugins/hazard-wildfire/pack.yaml` | Pin six module-scoped wildfire artifacts. | Partial activation is rejected. |
| `I08-S02-T02` | `plugins/hazard-wildfire/runtime/src/wildfire_screening.py` | Implement low-cost smoke/flame screening. | Hard-negative known answers pass. |
| `I08-S02-T03` | `plugins/hazard-wildfire/runtime/src/wildfire_confirmation.py` | Implement bounded confirmation and calibrated abstention. | Frozen event-level quality gate passes. |
| `I08-S02-T04` | `plugins/hazard-wildfire/incident/src/policy.py` | Implement candidate/observed/reviewed/resolved transitions with persistence and coverage. | Single-frame/external-only evidence cannot verify. |
| `I08-S02-T05` | `plugins/hazard-wildfire/client/src/vocabulary.ts` | Add labels, explanations and safety wording. | No official-warning claim appears. |
| `I08-S02-T06` | `plugins/hazard-wildfire/fixtures/conformance.yaml` | Add smoke, steam, cloud, glare, darkness, obstruction and camera-failure cases. | Workload/policy conformance passes. |

### I08-S03 — Create signed physical scenario

**Stage outcome:** The first vertical slice is deterministic, resettable and semantically checked.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I08-S03-T01` | `integration-tests/vertical-slices/physical-wildfire/scenario.yaml` | Define virtual time, camera stream, invariants, review command and reset. | Schema/signature validation passes. |
| `I08-S03-T02` | `integration-tests/vertical-slices/physical-wildfire/fixtures/camera-stream.jsonl` | Provide normal, hard-negative, trigger and recovery observations. | Hashes and rights metadata are stable. |
| `I08-S03-T03` | `integration-tests/vertical-slices/physical-wildfire/expected.yaml` | Define semantic outcomes, latency budget and authority invariants. | No random ID/wall-clock dependency. |
| `I08-S03-T04` | `apps/sentinel-scenario-runner/src/sentinel_scenario_runner/main.py` | Execute signed scenarios, verify invariants and reset stores. | Two clean runs match semantically. |
| `I08-S03-T05` | `integration-tests/vertical-slices/physical-wildfire/test_scenario.py` | Assert end-to-end causation, incident version and UI outcome. | Failure identifies first broken boundary. |

### I08-S04 — Complete review and evaluator proof

**Stage outcome:** Evaluators see authoritative state, reasons, provenance and measured timing.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I08-S04-T01` | `modules/client-applications/web/src/features/hazard-wildfire.tsx` | Render wildfire status, temporal evidence, coverage and review. | Model score is not official certainty. |
| `I08-S04-T02` | `modules/client-applications/mobile-shell/src/features/hazard-wildfire.tsx` | Render equivalent mobile semantics. | Parity snapshot matches web. |
| `I08-S04-T03` | `modules/client-applications/web/src/features/judge-proof.tsx` | Render correlation chain, hashes, capture age and gate status. | No fabricated benchmark value. |
| `I08-S04-T04` | `integration-tests/vertical-slices/physical-wildfire/test_client_review.py` | Exercise review, stale conflict and projection update. | Concurrent stale review visibly conflicts. |

### I08 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run the entire repository gate plus all physical-path pairwise suites and wildfire vertical slice twice after clean reset.
- Inject camera obstruction, worker failure, API disconnect and offline review; verify explicit degradation/recovery.
- Measure capture-to-incident and capture-to-client on the declared environment.
- Do not proceed until accessibility, provenance and full regression are green.

**Mandatory evidence:**

- Signed wildfire pack
- Physical vertical transcript
- End-to-end trace
- Latency/RSS evidence
- Client parity evidence
- Green full regression gate

**Completion rule:** `I08` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I09 — Structured analysis, claims, lineage and trust factors

**Increment:** Module 02 transforms structured source items into traceable claims, derivation graphs and multidimensional trust assessments, using Module 03 for learned jobs without deciding incident truth.

**Entry condition:** I08 is demonstrated; Collector, Runtime and Incident contracts are stable.

### I09-S01 — Implement analysis DAG and owned artifacts

**Stage outcome:** Recipes are immutable DAGs with explicit partial completion and content-addressed outputs.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I09-S01-T01` | `modules/analysis-enrichment-engine/migrations/0001_analysis_state.sql` | Create jobs, DAG, artifacts, lineage, claims, trust and idempotency tables. | Current/N-1 migrations pass. |
| `I09-S01-T02` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/domain/recipe.py` | Define node types, determinism, budgets, cancellation and failure policy. | Cycles/unbounded nodes fail. |
| `I09-S01-T03` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/dag.py` | Execute deterministic and Runtime nodes with partial/abstained semantics. | Missing nodes appear in limitations. |
| `I09-S01-T04` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/adapters/artifact_store.py` | Write immutable derived artifacts with parent hashes. | Original content is never overwritten. |
| `I09-S01-T05` | `modules/analysis-enrichment-engine/tests/property/test_dag_state_machine.py` | Generate retries, cancellation, duplicates and restart. | Terminal/idempotency invariants hold. |

### I09-S02 — Implement structured claims

**Stage outcome:** Text and records produce time/location/entity claims linked to exact source spans.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I09-S02-T01` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/structured_parser.py` | Parse bounded JSON/XML/text fields. | Malformed/oversized structures are contained. |
| `I09-S02-T02` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/claim_extraction.py` | Create normalized claims with exact source span. | Every claim resolves to immutable source/recipe. |
| `I09-S02-T03` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/translation.py` | Create translation as derived artifact preserving original. | Original is never replaced. |
| `I09-S02-T04` | `modules/analysis-enrichment-engine/tests/golden/test_structured_claims.py` | Add multilingual, ambiguous, missing and contradictory fixtures. | Golden outputs are deterministic. |

### I09-S03 — Implement lineage and trust

**Stage outcome:** Duplicates/reposts are grouped and trust dimensions remain separate.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I09-S03-T01` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/domain/lineage.py` | Represent derivation, repost, duplicate and family edges. | Cycles and false independence fail. |
| `I09-S03-T02` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/lineage_resolution.py` | Resolve exact/near duplicates with uncertainty. | Compression/translation/repost preserve family. |
| `I09-S03-T03` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/trust.py` | Compute standing, integrity, freshness, extraction, independence and corroboration. | No factor substitutes silently. |
| `I09-S03-T04` | `modules/analysis-enrichment-engine/tests/metamorphic/test_lineage_and_trust.py` | Test clipping, translation, reorder, compression and repost. | Changes are explainable and traceable. |

### I09-S04 — Integrate Analyzer boundaries

**Stage outcome:** Real pairwise workflows preserve rights, jobs, lineage and authority.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I09-S04-T01` | `integration-tests/pairwise/analyzer-runtime/test_jobs.py` | Test requests/results, cancellation, fallback and partial DAG. | Causation/artifacts are preserved. |
| `I09-S04-T02` | `integration-tests/pairwise/collector-analyzer/test_structured.py` | Test rights, hostile/partial input and deduplication. | Analyzer cannot acquire sources directly. |
| `I09-S04-T03` | `integration-tests/pairwise/analyzer-incident/test_analysis_bundle.py` | Test support, contradiction, lineage and no truth bypass. | Low-trust bundle yields at most a lead. |
| `I09-S04-T04` | `modules/analysis-enrichment-engine/contracts/asyncapi.yaml` | Publish inputs, model correlation and bundle channels. | Current/N-1 verification passes. |
| `I09-S04-T05` | `modules/analysis-enrichment-engine/README.md` | Document DAG, partial output, lineage, trust and resource deferral. | It states Analyzer is not truth authority. |

### I09 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior gates plus Analyzer property, golden, translation/lineage metamorphic, component, contracts and three pairwise suites.
- Inject duplicate/repost and contradiction; preserve branches and evidence families.
- Interrupt Runtime jobs and restart Analyzer; verify partial limitations and idempotent completion.
- Re-run wildfire slice to prove no Tier A regression.

**Mandatory evidence:**

- DAG transcript
- Golden claims/translation report
- Lineage/trust report
- Analyzer pairwise verification
- Wildfire regression
- Green full regression gate

**Completion rule:** `I09` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I10 — External multimodal intelligence: image, audio and video evidence

**Increment:** Rights-gated media is quarantined, bounded, analyzed through OCR/ASR/keyframes and Runtime jobs, converted into timestamped claims and shown as non-authoritative leads with trust and lineage.

**Entry condition:** I09 is demonstrated and the structured analysis path is stable.

### I10-S01 — Implement image analysis

**Stage outcome:** Images produce bounded quality/privacy, OCR and visual regions with traceable abstention.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I10-S01-T01` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/image_analysis.py` | Implement format/dimension checks, privacy transform and OCR/visual requests. | Decompression bombs fail within budgets. |
| `I10-S01-T02` | `plugins/analyzer-ocr-reference/src/sentinel_ocr_reference/plugin.py` | Implement bounded OCR with region provenance. | Rotation/compression/quality tests pass or abstain. |
| `I10-S01-T03` | `plugins/runtime-image-reference/src/sentinel_image_reference/plugin.py` | Implement qualified compact image workload. | Quality and Arm latency gates pass. |
| `I10-S01-T04` | `modules/analysis-enrichment-engine/tests/golden/test_image_analysis.py` | Add text, hazard-like, manipulated, private and poor-quality fixtures. | Every finding has region/source hash. |

### I10-S02 — Implement audio analysis

**Stage outcome:** Audio is segmented and transcribed with timestamped coverage gaps.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I10-S02-T01` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/audio_analysis.py` | Implement codec/duration checks, segmentation and ASR requests. | Long/corrupt audio fails safely. |
| `I10-S02-T02` | `plugins/analyzer-asr-reference/src/sentinel_asr_reference/plugin.py` | Implement ASR with segment provenance. | Noise/clipping/language tests pass or abstain. |
| `I10-S02-T03` | `plugins/runtime-audio-reference/src/sentinel_audio_reference/plugin.py` | Implement qualified compact audio workload. | Known-answer/resource gates pass. |
| `I10-S02-T04` | `modules/analysis-enrichment-engine/tests/golden/test_audio_analysis.py` | Add speech, noise, silence, clipping and corrupt fixtures. | No-output becomes abstention/gap. |

### I10-S03 — Implement video analysis

**Stage outcome:** Video uses bounded metadata, keyframes and audio segments, never unbounded full-video processing.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I10-S03-T01` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/video_analysis.py` | Implement duration/codec/frame budget and linked audio. | Frame/wall budgets hold. |
| `I10-S03-T02` | `plugins/analyzer-keyframe-reference/src/sentinel_keyframe_reference/plugin.py` | Implement deterministic keyframe extraction. | Repeated runs select same frames. |
| `I10-S03-T03` | `modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/application/media_integrity.py` | Record inconsistency, manipulation/OOD and missing intervals as weakening factors. | They never create positive truth. |
| `I10-S03-T04` | `modules/analysis-enrichment-engine/tests/golden/test_video_analysis.py` | Add normal, hazard-like, reposted, edited and corrupt fixtures. | Findings resolve to timestamps/keyframes. |

### I10-S04 — Implement capture, upload and rendering

**Stage outcome:** Users consent, upload and follow quarantine/analysis without exposing raw private content.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I10-S04-T01` | `modules/client-applications/mobile-shell/src/features/field-report.tsx` | Implement capture preview, consent, upload and status. | Permission follows explicit user action. |
| `I10-S04-T02` | `modules/client-applications/web/src/features/upload-evidence.tsx` | Implement bounded upload progress/failure/quarantine state. | Unsupported/oversized files fail early. |
| `I10-S04-T03` | `modules/client-applications/shared-domain/src/evidence-rendering.ts` | Define sanitized modality renderers and gap presentation. | No unrestricted raw URL access. |
| `I10-S04-T04` | `modules/rest-api-integration-gateway/src/sentinel_rest_api_integration_gateway/http/uploads.py` | Implement authorized upload session and Collector handoff. | API does not analyze or become source owner. |
| `I10-S04-T05` | `modules/rest-api-integration-gateway/tests/security/test_uploads.py` | Test type confusion, size, auth, privacy and interruption. | Hostile bytes reach only quarantine. |

### I10-S05 — Create external evidence vertical slice

**Stage outcome:** A signed media fixture becomes a traceable lead and trust UI without independent verification.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I10-S05-T01` | `integration-tests/vertical-slices/external-evidence/scenario.yaml` | Define rights-gated media, analysis, Runtime, Incident lead and review. | Includes backlog/outage/reset. |
| `I10-S05-T02` | `integration-tests/vertical-slices/external-evidence/expected.yaml` | Define provenance, trust dimensions, gaps and no-bypass invariants. | Outcomes are semantic/deterministic. |
| `I10-S05-T03` | `integration-tests/vertical-slices/external-evidence/test_scenario.py` | Execute image/audio/video branches. | Original/derived lineage is complete. |
| `I10-S05-T04` | `modules/client-applications/web/src/features/evidence-review.tsx` | Render lineage, spans/segments, trust and contradictions. | Source and analysis uncertainty differ. |
| `I10-S05-T05` | `modules/client-applications/mobile-shell/src/features/evidence-review.tsx` | Render accessible mobile evidence review. | Audio/video have text alternatives. |

### I10 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- Run all prior gates plus media golden/metamorphic, parser/resource isolation, upload security, Analyzer↔Runtime load and external evidence slice.
- Create external-media backlog while wildfire runs; Tier A must hold or explicit overload appears.
- Attempt verify/resolve using only low-trust media; Incident must refuse.
- Run both mandatory vertical slices, accessibility and complete regression.

**Mandatory evidence:**

- Multimodal corpus report
- Resource-isolation report
- Upload security evidence
- External-evidence transcript
- Trust/lineage UI evidence
- Two-slice regression gate

**Completion rule:** `I10` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I11 — Flood hazard pack and multi-hazard coexistence

**Increment:** Add a complete flood capability while preserving wildfire behavior and shared platform semantics.

**Entry condition:** `I10` is complete and the physical plus external-evidence vertical slices are green.

### I11.S01 — Flood collection and quality semantics

**Stage outcome:** Water-level, rainfall and flow observations are normalized with explicit units, quality and staleness.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I11.S01.T01` | `contracts/schemas/observation/flood-water-level.schema.json` | Add canonical water-level, datum, uncertainty and unit fields. | Schema positive/negative fixtures pass. |
| `I11.S01.T02` | `contracts/schemas/observation/flood-rainfall.schema.json` | Add rainfall accumulation, interval and intensity representation. | Unit and interval property tests pass. |
| `I11.S01.T03` | `contracts/schemas/observation/flood-flow.schema.json` | Add stream-flow and discharge observation representation. | Boundary and unit fixtures pass. |
| `I11.S01.T04` | `modules/collector/src/mappings/flood.py` | Map supported gauges and weather inputs into canonical envelopes. | Golden mapping tests are byte-stable. |
| `I11.S01.T05` | `modules/collector/src/quality/flood.py` | Implement range, jump, datum, freshness and sensor-health checks. | Fault-injection quality tests pass. |
| `I11.S01.T06` | `fixtures/flood/collection-cases.jsonl` | Add nominal, stale, impossible, missing-datum and reset cases. | Fixture validator accepts all intended outcomes. |
| `I11.S01.T07` | `modules/collector/tests/test_flood_collection.py` | Test mapping, quality flags, replay and deduplication. | Collector flood suite passes. |

### I11.S02 — Flood analysis and runtime qualification

**Stage outcome:** Deterministic flood rules and any optional model execute only under site-qualified profiles and abstain safely.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I11.S02.T01` | `modules/analyzer/src/hazards/flood/rules.py` | Implement level, rise-rate, rainfall and corroboration claim rules. | Known-answer and boundary tests pass. |
| `I11.S02.T02` | `modules/analyzer/src/hazards/flood/evidence.py` | Compose claims without treating missing gauges as normal or safe. | Missing-input and contradiction tests pass. |
| `I11.S02.T03` | `modules/runtime/config/profiles/flood-site-qualified.yaml` | Define accepted sensors, datum assumptions, resource envelope and quality thresholds. | Profile schema and qualification checks pass. |
| `I11.S02.T04` | `modules/runtime/src/workloads/flood_compact.py` | Register the optional compact flood workload with explicit abstention outputs. | Runtime workload contract tests pass. |
| `I11.S02.T05` | `fixtures/flood/known-answers.json` | Add deterministic site-qualified known-answer vectors. | Known-answer checksum and result tests pass. |
| `I11.S02.T06` | `modules/runtime/tests/test_flood_qualification.py` | Reject unqualified sites, stale profiles and unsupported units. | Negative qualification tests pass. |
| `I11.S02.T07` | `modules/analyzer/tests/test_flood_claims.py` | Test claims, conflicts, confidence bounds and abstention. | Analyzer flood suite passes. |

### I11.S03 — Flood incident policy and atomic pack

**Stage outcome:** Flood incidents have coverage-aware lifecycle rules and are activated as one atomic six-module hazard pack.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I11.S03.T01` | `modules/incident/src/policies/flood.py` | Implement create, escalate, downgrade, resolve and reopen policy. | Transition model/property tests pass. |
| `I11.S03.T02` | `modules/incident/src/policies/coverage.py` | Require adequate recent coverage before downgrade, resolution or safe status. | No-false-safe invariant tests pass. |
| `I11.S03.T03` | `plugins/hazards/flood/manifest.yaml` | Declare compatible collector, analyzer, runtime, incident, API and client components. | Pack manifest and dependency validation pass. |
| `I11.S03.T04` | `plugins/hazards/flood/incident-policy.yaml` | Define thresholds, corroboration, review and alert-budget policy. | Policy compiler and golden tests pass. |
| `I11.S03.T05` | `plugins/hazards/flood/conformance.yaml` | Declare pack-level conformance cases and expected outputs. | Pack conformance runner passes. |
| `I11.S03.T06` | `modules/incident/tests/test_flood_policy.py` | Test hysteresis, coverage loss, conflicts and resolution gates. | Incident flood suite passes. |

### I11.S04 — Flood API and client experience

**Stage outcome:** API, web and mobile expose the same flood vocabulary, evidence and degraded-state semantics.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I11.S04.T01` | `contracts/openapi/components/schemas/FloodIncidentProjection.yaml` | Define flood-specific projection fields and evidence summaries. | OpenAPI lint and generated bindings pass. |
| `I11.S04.T02` | `modules/api/src/projections/flood.py` | Map incident projections without inventing absent measurements. | Projection golden tests pass. |
| `I11.S04.T03` | `modules/client-shared/src/hazards/flood.ts` | Define shared labels, units, severity and action semantics. | Type and vocabulary tests pass. |
| `I11.S04.T04` | `apps/web/src/features/incidents/FloodIncidentView.tsx` | Render water levels, trends, coverage and evidence uncertainty. | Component and accessibility tests pass. |
| `I11.S04.T05` | `apps/mobile/src/features/incidents/FloodIncidentScreen.tsx` | Render equivalent offline-capable flood details. | Mobile component and snapshot tests pass. |
| `I11.S04.T06` | `integration-tests/contracts/test_flood_api_client.py` | Verify generated-client and projection compatibility. | Consumer/provider contract passes. |

### I11.S05 — Flood vertical slice and coexistence

**Stage outcome:** A reproducible flood scenario works end to end and does not interfere with wildfire incidents.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I11.S05.T01` | `integration-tests/scenarios/flood-river-rise.yaml` | Describe normal, rising, warning, sensor loss, recovery and resolution phases. | Scenario schema validation passes. |
| `I11.S05.T02` | `integration-tests/expected/flood-river-rise.json` | Define expected claims, transitions, alerts and client states. | Expected-output validator passes. |
| `I11.S05.T03` | `integration-tests/vertical/test_flood_slice.py` | Execute Collector→Analyzer/Runtime→Incident→API→Clients. | Flood vertical test passes. |
| `I11.S05.T04` | `integration-tests/scenarios/wildfire-flood-concurrent.yaml` | Define concurrent independent wildfire and flood signals. | Scenario validates and remains deterministic. |
| `I11.S05.T05` | `integration-tests/vertical/test_multi_hazard_isolation.py` | Verify ownership, alert budgets and projections remain hazard-isolated. | Concurrency/isolation test passes. |
| `I11.S05.T06` | `docs/runbooks/flood-pack.md` | Document site qualification, deployment, degraded modes and rollback. | Documentation checks and executable commands pass. |

### I11 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs every suite activated through `I11`, including all prior wildfire and multimodal regressions.
- `make test-hazard HAZARD=flood PROFILE=test-standalone` passes deterministic, qualification and policy tests.
- `make test-vertical SCENARIO=flood-river-rise` passes from a clean state.
- `make test-vertical SCENARIO=wildfire-flood-concurrent` proves hazard isolation and bounded contention.
- Sensor outage, stale datum and missing coverage cases never produce a false-safe downgrade or resolution.
- The flood pack is installable, activatable, rejectable and rollback-safe as one atomic compatibility unit.
- Web and mobile accessibility checks pass for every flood state, including unknown and degraded.

**Mandatory evidence:**

- Flood pack conformance report and manifest digest
- Site-qualification and abstention report
- Flood vertical-slice event journal and projection snapshots
- Concurrent-hazard resource and isolation report
- Updated cumulative test inventory

**Completion rule:** `I11` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I12 — Earthquake post-onset detection and priority scheduling

**Increment:** Add post-onset seismic detection and incident handling with explicit prohibition of prediction claims.

**Entry condition:** `I11` is complete and the multi-hazard flood/wildfire regression gate is green.

### I12.S01 — Seismic acquisition and normalization

**Stage outcome:** Accelerometer and seismic trigger inputs are normalized with calibration, timing and quality metadata.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I12.S01.T01` | `contracts/schemas/observation/seismic-motion.schema.json` | Define acceleration, sample rate, axis, clock quality and calibration fields. | Schema fixture suite passes. |
| `I12.S01.T02` | `modules/collector/src/protocols/seismic.py` | Decode supported seismic/IMU frames with bounded parsing. | Protocol fuzz and golden tests pass. |
| `I12.S01.T03` | `modules/collector/src/mappings/seismic.py` | Map decoded samples and trigger summaries into canonical envelopes. | Mapping golden tests pass. |
| `I12.S01.T04` | `modules/collector/src/quality/seismic.py` | Check clipping, clock drift, calibration, gaps and sensor health. | Quality fault tests pass. |
| `I12.S01.T05` | `fixtures/earthquake/seismic-cases.jsonl` | Add noise, impulse, clipping, clock-loss and true-event fixtures. | Fixture validation passes. |
| `I12.S01.T06` | `modules/collector/tests/test_seismic_collection.py` | Test decode, normalization, deduplication and replay. | Collector seismic suite passes. |

### I12.S02 — Post-onset detection and Arm runtime priority

**Stage outcome:** Seismic triggers are detected after motion begins and execute under a bounded Tier-A resource policy.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I12.S02.T01` | `modules/analyzer/src/hazards/earthquake/trigger.py` | Implement deterministic onset and corroboration claims. | Known-answer and false-trigger tests pass. |
| `I12.S02.T02` | `modules/runtime/src/workloads/seismic_classifier.py` | Register compact post-onset classifier with calibrated abstention. | Workload contract and known-answer tests pass. |
| `I12.S02.T03` | `modules/runtime/config/profiles/seismic-tier-a.yaml` | Define latency, CPU, memory, queue and quality envelope for highest-priority execution. | Profile validation and budget tests pass. |
| `I12.S02.T04` | `modules/runtime/src/scheduler/priority.py` | Reserve bounded Tier-A capacity without starving mandatory safety workloads. | Scheduling property and starvation tests pass. |
| `I12.S02.T05` | `fixtures/earthquake/known-answers.json` | Add deterministic trigger and non-trigger vectors. | Checksum and expected-result tests pass. |
| `I12.S02.T06` | `modules/runtime/tests/test_seismic_priority.py` | Test backlog pressure, preemption, deadlines and degradation. | Runtime priority suite passes. |
| `I12.S02.T07` | `modules/analyzer/tests/test_earthquake_claims.py` | Test timing, confidence, corroboration and explicit post-onset semantics. | Analyzer earthquake suite passes. |

### I12.S03 — Earthquake incident policy and language safety

**Stage outcome:** Incident lifecycle communicates detected motion and operational impact without prediction or false certainty.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I12.S03.T01` | `modules/incident/src/policies/earthquake.py` | Implement detected-motion lifecycle, review, aftershock updates and resolution rules. | Transition and replay tests pass. |
| `I12.S03.T02` | `plugins/hazards/earthquake/manifest.yaml` | Declare atomic six-module earthquake pack compatibility. | Pack validation passes. |
| `I12.S03.T03` | `plugins/hazards/earthquake/incident-policy.yaml` | Define trigger, corroboration, review, alert and resolution policy. | Policy compile and conformance tests pass. |
| `I12.S03.T04` | `modules/client-shared/src/hazards/earthquake.ts` | Use post-onset labels and prohibit predictive wording. | Vocabulary lint tests pass. |
| `I12.S03.T05` | `tools/lint/check_earthquake_language.py` | Reject prohibited prediction or advance-warning claims in code, UI and docs. | Positive and negative lint fixtures pass. |
| `I12.S03.T06` | `modules/incident/tests/test_earthquake_policy.py` | Test duplicate triggers, aftershocks, sensor loss and resolution. | Incident earthquake suite passes. |

### I12.S04 — Earthquake API and clients

**Stage outcome:** Clients receive low-latency resumable updates with consistent detected-motion and degraded-state semantics.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I12.S04.T01` | `contracts/openapi/components/schemas/EarthquakeIncidentProjection.yaml` | Define motion, timing, corroboration and impact fields. | OpenAPI and generated-client tests pass. |
| `I12.S04.T02` | `modules/api/src/projections/earthquake.py` | Expose journal-derived earthquake projections and evidence. | Projection golden tests pass. |
| `I12.S04.T03` | `apps/web/src/features/incidents/EarthquakeIncidentView.tsx` | Render detected motion, timing, evidence and safety guidance. | Accessibility and component tests pass. |
| `I12.S04.T04` | `apps/mobile/src/features/incidents/EarthquakeIncidentScreen.tsx` | Render equivalent mobile/offline state and updates. | Mobile component tests pass. |
| `I12.S04.T05` | `integration-tests/contracts/test_earthquake_api_client.py` | Verify API-client schema and semantic compatibility. | Consumer/provider tests pass. |

### I12.S05 — Backlog-stressed earthquake vertical slice

**Stage outcome:** A seismic trigger remains timely and correct during external-media backlog, worker restart and competing hazards.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I12.S05.T01` | `integration-tests/scenarios/earthquake-under-backlog.yaml` | Define media backlog, seismic onset, worker restart and recovery. | Scenario schema passes. |
| `I12.S05.T02` | `integration-tests/expected/earthquake-under-backlog.json` | Define deadlines, transitions, degraded states and final recovery. | Expected validator passes. |
| `I12.S05.T03` | `integration-tests/vertical/test_earthquake_slice.py` | Execute the full post-onset vertical slice under pressure. | Vertical test meets correctness and latency gates. |
| `I12.S05.T04` | `integration-tests/performance/test_tier_a_latency.py` | Measure bounded p50/p95/p99 latency under declared Arm profile. | Performance thresholds pass. |
| `I12.S05.T05` | `docs/runbooks/earthquake-pack.md` | Document post-onset scope, deployment, limitations and rollback. | Docs tests and language lint pass. |

### I12 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs the cumulative suite through `I12` with no removed or muted tests.
- `make test-hazard HAZARD=earthquake PROFILE=test-standalone` passes trigger, policy and vocabulary tests.
- `make test-vertical SCENARIO=earthquake-under-backlog` passes with the declared Tier-A latency envelope.
- The earthquake-language linter scans source, schemas, fixtures, UI, docs and generated artifacts and finds no predictive claim.
- Collector and runtime restarts during onset preserve idempotency, ordering evidence and final incident truth.
- Concurrent wildfire, flood and earthquake signals remain isolated while Tier-A scheduling avoids starvation.
- Unsupported calibration, clipping or clock quality produces explicit degraded/unknown state rather than confidence inflation.

**Mandatory evidence:**

- Post-onset scope/language scan report
- Tier-A latency and starvation report
- Seismic known-answer and qualification results
- Earthquake vertical-slice journal and client snapshots
- Cumulative multi-hazard regression report

**Completion rule:** `I12` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I13 — Landslide susceptibility, saturation and observed movement

**Increment:** Add a landslide pack that distinctly represents susceptibility, saturation and observed movement without conflating them.

**Entry condition:** `I12` is complete and all three existing hazard packs pass cumulative regression.

### I13.S01 — Site profile and observation quality

**Stage outcome:** Slope, rainfall, soil moisture and movement observations are site-qualified and quality-scored.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I13.S01.T01` | `contracts/schemas/hazards/landslide-site-profile.schema.json` | Define slope units, geometry, susceptibility provenance, sensors and validity. | Schema positive/negative tests pass. |
| `I13.S01.T02` | `modules/collector/src/mappings/landslide.py` | Normalize rainfall, moisture, inclinometer and displacement inputs. | Golden mapping tests pass. |
| `I13.S01.T03` | `modules/collector/src/quality/landslide.py` | Check calibration, drift, stuck values, geometry and freshness. | Quality fault-injection tests pass. |
| `I13.S01.T04` | `fixtures/landslide/site-profiles.json` | Add valid, expired, incomplete and incompatible site profiles. | Fixture validation passes. |
| `I13.S01.T05` | `fixtures/landslide/observation-cases.jsonl` | Add dry, saturated, movement, drift and outage sequences. | Fixture validator passes. |
| `I13.S01.T06` | `modules/collector/tests/test_landslide_collection.py` | Test mappings, quality, profile binding and replay. | Collector landslide suite passes. |

### I13.S02 — Landslide analysis and adaptation guard

**Stage outcome:** Analysis distinguishes predisposition from dynamic saturation and actual movement, with no silent online adaptation.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I13.S02.T01` | `modules/analyzer/src/hazards/landslide/saturation.py` | Implement saturation and antecedent-rainfall claims. | Boundary and known-answer tests pass. |
| `I13.S02.T02` | `modules/analyzer/src/hazards/landslide/movement.py` | Implement corroborated observed-movement claims. | Noise, drift and true-movement tests pass. |
| `I13.S02.T03` | `modules/analyzer/src/hazards/landslide/fusion.py` | Fuse susceptibility, saturation and movement without promoting susceptibility alone to an incident. | Invariant and conflict tests pass. |
| `I13.S02.T04` | `modules/runtime/config/profiles/landslide-site-qualified.yaml` | Define allowed site profile, workload and quality envelope. | Qualification validation passes. |
| `I13.S02.T05` | `modules/runtime/src/guards/model_update.py` | Reject undeclared parameter or model changes during operation. | Mutation and tamper tests pass. |
| `I13.S02.T06` | `modules/analyzer/tests/test_landslide_claims.py` | Test semantic separation, confidence and missing-data behavior. | Analyzer landslide suite passes. |
| `I13.S02.T07` | `modules/runtime/tests/test_no_silent_adaptation.py` | Prove runtime state cannot silently alter approved models or thresholds. | Guard tests pass. |

### I13.S03 — Landslide incident policy and pack

**Stage outcome:** Incident transitions require dynamic evidence and preserve explicit uncertainty and coverage.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I13.S03.T01` | `modules/incident/src/policies/landslide.py` | Implement watch, detected movement, escalation, downgrade and resolution transitions. | State-machine/property tests pass. |
| `I13.S03.T02` | `plugins/hazards/landslide/manifest.yaml` | Declare atomic pack compatibility and site-profile dependency. | Manifest validation passes. |
| `I13.S03.T03` | `plugins/hazards/landslide/incident-policy.yaml` | Define evidence, corroboration, review and coverage gates. | Policy compile and conformance pass. |
| `I13.S03.T04` | `plugins/hazards/landslide/conformance.yaml` | Add susceptibility-only, saturation, movement, drift and outage cases. | Pack conformance passes. |
| `I13.S03.T05` | `modules/incident/tests/test_landslide_policy.py` | Test no-incident susceptibility, movement confirmation and safe resolution. | Incident landslide suite passes. |

### I13.S04 — Landslide API and client semantics

**Stage outcome:** The UI clearly separates susceptibility context, saturation state and observed movement evidence.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I13.S04.T01` | `contracts/openapi/components/schemas/LandslideIncidentProjection.yaml` | Define distinct susceptibility, saturation and movement fields. | OpenAPI lint and generation pass. |
| `I13.S04.T02` | `modules/api/src/projections/landslide.py` | Map journal state without collapsing distinct evidence types. | Projection golden tests pass. |
| `I13.S04.T03` | `modules/client-shared/src/hazards/landslide.ts` | Define shared terminology and severity/action mapping. | Vocabulary tests pass. |
| `I13.S04.T04` | `apps/web/src/features/incidents/LandslideIncidentView.tsx` | Render distinct evidence groups, site validity and unknown states. | Component/accessibility tests pass. |
| `I13.S04.T05` | `apps/mobile/src/features/incidents/LandslideIncidentScreen.tsx` | Render equivalent offline-capable mobile view. | Mobile tests pass. |
| `I13.S04.T06` | `integration-tests/contracts/test_landslide_api_client.py` | Verify schema and semantic compatibility. | Consumer/provider tests pass. |

### I13.S05 — Landslide vertical slice and drift scenario

**Stage outcome:** The end-to-end system detects real movement, resists drift, and does not incident on static susceptibility alone.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I13.S05.T01` | `integration-tests/scenarios/landslide-saturation-movement.yaml` | Define susceptibility, rainfall, saturation, drift, movement and recovery. | Scenario validates. |
| `I13.S05.T02` | `integration-tests/expected/landslide-saturation-movement.json` | Define claims, non-events, transitions and client states. | Expected validator passes. |
| `I13.S05.T03` | `integration-tests/vertical/test_landslide_slice.py` | Execute the complete landslide vertical slice. | Vertical test passes. |
| `I13.S05.T04` | `integration-tests/vertical/test_landslide_drift_guard.py` | Prove drift and susceptibility alone cannot create a confirmed incident. | Negative vertical test passes. |
| `I13.S05.T05` | `docs/runbooks/landslide-pack.md` | Document site qualification, semantic distinctions and rollback. | Docs and terminology checks pass. |

### I13 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs all cumulative suites through `I13`.
- `make test-hazard HAZARD=landslide PROFILE=test-standalone` passes collection, analysis, runtime, incident and UI conformance.
- `make test-vertical SCENARIO=landslide-saturation-movement` passes deterministically.
- Susceptibility alone, stale profiles, drift and missing movement coverage cannot create a confirmed movement incident.
- Any runtime model or threshold mutation is rejected, audited and visible; no silent adaptation is possible.
- All four hazard packs coexist without cross-pack state leakage or incompatible vocabulary.
- Compact and test-standalone profiles produce semantically equivalent incident outcomes.

**Mandatory evidence:**

- Landslide pack conformance and site-qualification report
- No-silent-adaptation proof
- Drift/susceptibility negative-test report
- Landslide vertical journal and projection snapshots
- Cumulative four-hazard regression report

**Completion rule:** `I13` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I14 — Extensible source ecosystem and rights-aware acquisition

**Increment:** Add official, scientific, publisher, feed, webhook and opt-in community sources through governed connectors.

**Entry condition:** `I13` is complete and every active hazard pack passes in the cumulative gate.

### I14.S01 — Source registry and acquisition governance

**Stage outcome:** Every connector has declared identity, rights, reliability class, rate limits, retention and health semantics.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I14.S01.T01` | `contracts/schemas/sources/source-descriptor.schema.json` | Define source identity, authority class, rights, retention, geography and reliability metadata. | Schema fixtures pass. |
| `I14.S01.T02` | `contracts/schemas/sources/acquisition-policy.schema.json` | Define polling, webhook, backoff, rate, content and legal constraints. | Schema negative/positive tests pass. |
| `I14.S01.T03` | `modules/collector/src/registry/source_registry.py` | Load and validate source descriptors without connector-specific branching. | Registry unit/property tests pass. |
| `I14.S01.T04` | `modules/collector/src/policy/acquisition.py` | Enforce rights, allowlists, rate limits, content limits and retention at ingress. | Policy tests pass. |
| `I14.S01.T05` | `modules/collector/src/health/source_health.py` | Emit consistent source-health, staleness and backpressure events. | Health state-machine tests pass. |
| `I14.S01.T06` | `modules/collector/tests/test_source_governance.py` | Test denied rights, expired policy, rate limit and recovery. | Governance suite passes. |

### I14.S02 — Official and scientific connectors

**Stage outcome:** High-authority public feeds are integrated through replaceable connectors and canonical contracts.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I14.S02.T01` | `modules/collector/plugins/cap_like/connector.py` | Implement a CAP-like alert connector behind the source plugin interface. | Connector conformance and replay tests pass. |
| `I14.S02.T02` | `modules/collector/plugins/sensorthings/connector.py` | Implement OGC SensorThings 1.1 observation acquisition. | Pagination, unit and cursor tests pass. |
| `I14.S02.T03` | `modules/collector/plugins/scientific_feed/connector.py` | Implement configurable scientific JSON/CSV feed ingestion. | Malformed, schema-drift and retry tests pass. |
| `I14.S02.T04` | `plugins/sources/official-defaults/manifest.yaml` | Declare official connector versions, permissions and compatibility. | Plugin manifest validation passes. |
| `I14.S02.T05` | `fixtures/sources/official-replays.json` | Add offline deterministic replay responses and expected cursors. | Replay checksum tests pass. |
| `I14.S02.T06` | `modules/collector/tests/plugins/test_official_connectors.py` | Run the common connector conformance suite against all official connectors. | Plugin conformance passes. |

### I14.S03 — News, feeds and authorized publisher sources

**Stage outcome:** Lower-authority external information is collected with explicit provenance and cannot bypass trust policy.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I14.S03.T01` | `modules/collector/plugins/rss_atom/connector.py` | Implement bounded RSS/Atom collection with canonical links and publication time. | Feed parsing/fuzz tests pass. |
| `I14.S03.T02` | `modules/collector/plugins/authorized_webhook/connector.py` | Implement signed webhook ingestion with replay protection. | Signature, replay and size-limit tests pass. |
| `I14.S03.T03` | `modules/collector/plugins/publisher_api/connector.py` | Implement configurable authorized publisher API acquisition. | Cursor, backoff and rights tests pass. |
| `I14.S03.T04` | `modules/analyzer/src/trust/source_priors.py` | Map declared source classes to transparent priors without hard-coded truth. | Calibration and monotonicity tests pass. |
| `I14.S03.T05` | `modules/analyzer/src/trust/corroboration.py` | Corroborate independent reports while detecting likely copying or common origin. | Dependence and duplicate tests pass. |
| `I14.S03.T06` | `modules/analyzer/tests/test_external_source_trust.py` | Test source priors, provenance dependence and low-trust limits. | Trust suite passes. |

### I14.S04 — Opt-in community upload and operator controls

**Stage outcome:** Authorized users can submit evidence with consent, provenance, privacy controls and visible trust limits.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I14.S04.T01` | `contracts/openapi/paths/community-evidence.yaml` | Define authenticated upload, consent, status and deletion endpoints. | OpenAPI lint and generated client pass. |
| `I14.S04.T02` | `modules/api/src/routes/community_evidence.py` | Implement bounded upload orchestration and status responses. | Route auth, limit and error tests pass. |
| `I14.S04.T03` | `modules/collector/plugins/community_upload/connector.py` | Convert accepted uploads into rights-gated external source items. | Connector and retention tests pass. |
| `I14.S04.T04` | `apps/web/src/features/sources/CommunityEvidenceForm.tsx` | Add consent-aware upload and processing status UI. | Accessibility and form tests pass. |
| `I14.S04.T05` | `apps/mobile/src/features/sources/CommunityEvidenceScreen.tsx` | Add equivalent mobile capture/upload with offline queue. | Offline and component tests pass. |
| `I14.S04.T06` | `modules/client-shared/src/sources/sourceHealth.ts` | Define source mode, health, backlog and trust presentation. | Shared semantic tests pass. |

### I14.S05 — Source outage, replay and no-network judge proofs

**Stage outcome:** Connector behavior is deterministic under outage, replay, staleness and offline benchmark conditions.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I14.S05.T01` | `integration-tests/scenarios/source-ecosystem-outage.yaml` | Define official outage, news backlog, duplicate reports and recovery. | Scenario validates. |
| `I14.S05.T02` | `integration-tests/expected/source-ecosystem-outage.json` | Define source health, trust effects, queue behavior and recovery. | Expected validator passes. |
| `I14.S05.T03` | `integration-tests/vertical/test_source_ecosystem.py` | Execute governed multi-source acquisition through client display. | Vertical suite passes. |
| `I14.S05.T04` | `integration-tests/security/test_no_network_judges.py` | Prove test and benchmark judges complete with outbound network denied. | Network-isolation test passes. |
| `I14.S05.T05` | `docs/source-catalog.md` | Document source classes, rights assumptions, connectors and trust presentation. | Catalog validation and link checks pass. |
| `I14.S05.T06` | `docs/runbooks/source-outage.md` | Document outage, credential, quota, drift and recovery procedures. | Runbook command checks pass. |

### I14 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs all prior tests plus every source-plugin conformance suite.
- `make test-sources` passes official, scientific, publisher, feed, webhook and community connectors against the common contract.
- `make test-vertical SCENARIO=source-ecosystem-outage` passes with deterministic replay artifacts.
- Outbound network is disabled for judges and benchmarks; all required evidence is fixture-backed and reproducible.
- Rights denial, consent withdrawal, source staleness and rate limiting are enforced before analysis and fully audited.
- Low-trust or copied external reports cannot independently verify, resolve or mark an incident safe.
- All connector failures remain localized and source-health degradation is visible through API, web and mobile.

**Mandatory evidence:**

- Connector conformance matrix
- Source rights and retention policy report
- Trust calibration/dependence test report
- Network-isolated judge transcript
- Source-outage vertical journal and UI snapshots
- Updated source catalog digest

**Completion rule:** `I14` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I15 — Plugin lifecycle, atomic upgrades and isolated deployment

**Increment:** Complete module-scoped plugin managers, atomic hazard-pack lifecycle and semantically equivalent process isolation.

**Entry condition:** `I14` is complete and the governed source ecosystem passes cumulative regression.

### I15.S01 — Module-scoped plugin managers

**Stage outcome:** Each module discovers, validates, activates and quarantines only its own plugin type.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I15.S01.T01` | `modules/collector/src/plugins/manager.py` | Implement collector plugin discovery, compatibility checks and quarantine. | Collector plugin lifecycle tests pass. |
| `I15.S01.T02` | `modules/analyzer/src/plugins/manager.py` | Implement analyzer plugin discovery, capability checks and quarantine. | Analyzer plugin lifecycle tests pass. |
| `I15.S01.T03` | `modules/runtime/src/plugins/manager.py` | Implement workload plugin discovery, qualification checks and quarantine. | Runtime plugin lifecycle tests pass. |
| `I15.S01.T04` | `modules/incident/src/plugins/manager.py` | Implement policy plugin discovery, compilation and quarantine. | Incident plugin lifecycle tests pass. |
| `I15.S01.T05` | `modules/api/src/plugins/manager.py` | Implement projection/route extension discovery with boundary checks. | API plugin lifecycle tests pass. |
| `I15.S01.T06` | `modules/client-shared/src/plugins/manager.ts` | Implement client vocabulary/view registration with compatibility checks. | Client plugin lifecycle tests pass. |
| `I15.S01.T07` | `integration-tests/plugins/test_module_plugin_isolation.py` | Prove managers reject foreign module plugin types and implementation imports. | Architecture/plugin isolation test passes. |

### I15.S02 — Atomic hazard-pack activation and rollback

**Stage outcome:** A hazard pack is installed, verified, activated, upgraded or rolled back as one compatible unit.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I15.S02.T01` | `contracts/schemas/plugins/hazard-pack.schema.json` | Define component versions, contracts, dependencies, migrations and rollback metadata. | Schema fixture tests pass. |
| `I15.S02.T02` | `modules/api/src/admin/hazard_packs.py` | Implement authorized plan, install, activate, deactivate and rollback commands. | Admin command and authorization tests pass. |
| `I15.S02.T03` | `modules/incident/src/plugins/activation_journal.py` | Journal pack lifecycle decisions and active compatibility set. | Replay/idempotency tests pass. |
| `I15.S02.T04` | `tools/plugins/validate_pack.py` | Validate signatures, compatibility, contracts, migrations and conformance evidence. | CLI positive/negative tests pass. |
| `I15.S02.T05` | `tools/plugins/transactional_activate.py` | Stage and atomically switch a validated six-component pack. | Crash-point and rollback tests pass. |
| `I15.S02.T06` | `integration-tests/plugins/test_atomic_pack_upgrade.py` | Test compatible upgrade, incompatible rejection and interrupted rollback. | Atomic upgrade integration test passes. |
| `I15.S02.T07` | `docs/runbooks/hazard-pack-lifecycle.md` | Document plan, validate, activate, observe and rollback procedures. | Runbook commands execute in test profile. |

### I15.S03 — Isolated transport and artifact references

**Stage outcome:** Modules can run as separate processes over local framed transport without changing domain semantics.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I15.S03.T01` | `contracts/transport/framed-message.schema.json` | Define frame version, correlation, payload encoding, checksum and error fields. | Schema and malformed-frame tests pass. |
| `I15.S03.T02` | `sdk/python/sentinel_edge_transport/framing.py` | Implement bounded JSON/MessagePack framing over Unix domain sockets. | Unit, property and fuzz tests pass. |
| `I15.S03.T03` | `sdk/python/sentinel_edge_transport/artifacts.py` | Implement immutable large-artifact references with digest verification. | Tamper, expiry and cleanup tests pass. |
| `I15.S03.T04` | `modules/collector/src/adapters/isolated_output.py` | Publish collector contracts through framed local transport. | Adapter contract tests pass. |
| `I15.S03.T05` | `modules/analyzer/src/adapters/isolated_io.py` | Consume observations and publish analysis bundles via transport. | Adapter contract tests pass. |
| `I15.S03.T06` | `modules/runtime/src/adapters/isolated_io.py` | Serve workload execution through bounded framed requests. | Adapter contract/deadline tests pass. |
| `I15.S03.T07` | `modules/incident/src/adapters/isolated_io.py` | Consume evidence and publish journal/projection events via transport. | Adapter replay tests pass. |
| `I15.S03.T08` | `modules/api/src/adapters/isolated_incident.py` | Bridge API commands and projections to isolated incident service. | Adapter contract tests pass. |

### I15.S04 — Isolated profile orchestration

**Stage outcome:** A supervised multi-process profile starts, stops, recovers and reports health predictably.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I15.S04.T01` | `deploy/profiles/isolated.yaml` | Define process topology, sockets, stores, resource limits and readiness dependencies. | Profile schema and static checks pass. |
| `I15.S04.T02` | `apps/supervisor/src/main.py` | Implement process lifecycle, readiness, restart budget and ordered shutdown. | Supervisor unit/state tests pass. |
| `I15.S04.T03` | `apps/supervisor/src/health.py` | Aggregate module and channel health without hiding partial failure. | Health aggregation tests pass. |
| `I15.S04.T04` | `deploy/systemd/sentinel-edge.target` | Define production-oriented service ordering and hardening baseline. | Systemd verify/lint passes. |
| `I15.S04.T05` | `integration-tests/deployment/test_isolated_boot.py` | Test clean boot, partial startup, restart and shutdown. | Deployment integration tests pass. |
| `I15.S04.T06` | `integration-tests/deployment/test_profile_equivalence.py` | Compare compact and isolated domain outputs for identical input fixtures. | Semantic equivalence test passes. |

### I15.S05 — Isolation security and failure proofs

**Stage outcome:** Malformed peers, compromised plugins and transport faults remain bounded and recoverable.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I15.S05.T01` | `integration-tests/security/test_uds_peer_identity.py` | Verify socket permissions and peer identity enforcement. | Unauthorized peer tests pass. |
| `I15.S05.T02` | `integration-tests/fuzz/test_transport_frames.py` | Fuzz length, encoding, checksum and truncation handling. | No crash, hang or unbounded allocation. |
| `I15.S05.T03` | `integration-tests/plugins/test_malicious_plugin.py` | Test forbidden imports, excessive resources, malformed output and escape attempts. | Plugin is rejected or quarantined. |
| `I15.S05.T04` | `integration-tests/chaos/test_isolated_channel_failure.py` | Inject disconnects, duplicate frames, delays and artifact loss. | Recovery and degraded-state assertions pass. |
| `I15.S05.T05` | `docs/runbooks/isolated-deployment.md` | Document topology, health, diagnostics, recovery and rollback. | Executable runbook checks pass. |

### I15 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs the cumulative suite plus all plugin lifecycle, transport and deployment tests.
- `make test-plugins` validates every source and hazard pack, including malicious and incompatible fixtures.
- `make test-profile PROFILE=isolated` passes boot, health, restart and shutdown scenarios.
- `make test-equivalence PROFILES=compact,isolated` produces identical incident decisions and compatible client projections for the canonical corpus.
- Transport fuzzing finds no crash, deadlock, unbounded allocation, unauthenticated peer acceptance or unchecked artifact use.
- An interrupted pack activation always leaves either the old complete pack or the new complete pack active—never a mixed set.
- Every module can still be built and tested standalone without starting the other five.

**Mandatory evidence:**

- Plugin compatibility and conformance matrix
- Atomic activation crash-point report
- Compact-versus-isolated semantic diff
- Transport fuzz and peer-identity report
- Isolated boot/recovery transcript
- Signed active-pack inventory

**Completion rule:** `I15` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I16 — Resilience, offline operation, recovery and whole-solution chaos

**Increment:** Prove deterministic recovery through simultaneous outages, restarts, corruption attempts and resource pressure.

**Entry condition:** `I15` is complete and compact/isolated semantic equivalence is green.

### I16.S01 — Deterministic fault model and recovery coordination

**Stage outcome:** Fault injection and recovery decisions are reproducible, observable and bounded.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I16.S01.T01` | `integration-tests/chaos/fault-plan.schema.json` | Define deterministic fault time, target, duration, seed and expected observability. | Schema tests pass. |
| `I16.S01.T02` | `integration-tests/chaos/fault_injector.py` | Implement process, network, disk, clock, queue and artifact fault actions. | Injector unit and dry-run tests pass. |
| `I16.S01.T03` | `modules/incident/src/recovery/coordinator.py` | Coordinate replay, projection rebuild and outbox recovery without assuming healthy dependencies. | Recovery state-machine tests pass. |
| `I16.S01.T04` | `modules/incident/src/recovery/invariants.py` | Assert journal monotonicity, idempotency, causality and no false-safe after recovery. | Invariant property tests pass. |
| `I16.S01.T05` | `modules/api/src/recovery/subscription_resume.py` | Resume SSE/WS subscribers from durable cursors and report gaps explicitly. | Resume/gap tests pass. |
| `I16.S01.T06` | `integration-tests/chaos/test_recovery_coordinator.py` | Exercise overlapping faults and repeated recovery. | Deterministic recovery tests pass. |

### I16.S02 — Inbox, outbox and cursor crash matrices

**Stage outcome:** Every durable message boundary survives crashes before and after each persistence/acknowledgement point.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I16.S02.T01` | `integration-tests/reliability/inbox_crash_matrix.py` | Enumerate consumer crash points around receive, validate, persist and acknowledge. | Matrix generator tests pass. |
| `I16.S02.T02` | `integration-tests/reliability/outbox_crash_matrix.py` | Enumerate producer crash points around journal, outbox, publish and mark-sent. | Matrix generator tests pass. |
| `I16.S02.T03` | `integration-tests/reliability/cursor_crash_matrix.py` | Enumerate source and client cursor crashes, duplicates and gaps. | Matrix generator tests pass. |
| `I16.S02.T04` | `integration-tests/reliability/test_inbox_matrix.py` | Prove no lost accepted input and safe duplicate handling. | All inbox crash cases pass. |
| `I16.S02.T05` | `integration-tests/reliability/test_outbox_matrix.py` | Prove journal/outbox consistency and eventual publication. | All outbox crash cases pass. |
| `I16.S02.T06` | `integration-tests/reliability/test_cursor_matrix.py` | Prove deterministic replay or explicit irrecoverable gap state. | All cursor cases pass. |

### I16.S03 — Offline-field deployment and client continuity

**Stage outcome:** The system operates locally through remote disconnection and reconciles safely on recovery.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I16.S03.T01` | `deploy/profiles/offline-field.yaml` | Define local-only dependencies, storage quotas, synchronization and degraded thresholds. | Profile validation passes. |
| `I16.S03.T02` | `modules/collector/src/sync/remote_buffer.py` | Buffer permitted outbound artifacts with bounded retention and backpressure. | Quota, expiry and replay tests pass. |
| `I16.S03.T03` | `modules/api/src/sync/reconciliation.py` | Expose explicit sync status and reconcile remote acknowledgements idempotently. | Reconciliation tests pass. |
| `I16.S03.T04` | `modules/client-shared/src/offline/reconciliation.ts` | Merge local actions and server truth using declared conflict rules. | Property and conflict tests pass. |
| `I16.S03.T05` | `apps/web/src/features/system/OfflineStatus.tsx` | Show local operation, backlog, data age and sync state accessibly. | Component/accessibility tests pass. |
| `I16.S03.T06` | `apps/mobile/src/features/system/OfflineStatusScreen.tsx` | Show equivalent mobile state and queued actions. | Mobile/offline tests pass. |
| `I16.S03.T07` | `integration-tests/deployment/test_offline_field.py` | Test disconnect, continued monitoring, bounded queues and reconnection. | Offline profile test passes. |

### I16.S04 — Signed whole-solution scenario

**Stage outcome:** The canonical M8 scenario exercises all modules, hazards, source classes, degradation and recovery.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I16.S04.T01` | `integration-tests/scenarios/whole-solution-m8.yaml` | Define normal monitoring, rain, smoke, seismic trigger, remote outage, sensor fault, media backlog, worker restart and recovery. | Scenario schema and determinism checks pass. |
| `I16.S04.T02` | `integration-tests/expected/whole-solution-m8.json` | Define every expected event, non-event, transition, alert, health state and final recovery. | Expected-output validator passes. |
| `I16.S04.T03` | `integration-tests/whole/test_m8_whole_solution.py` | Execute the complete scenario against compact and isolated profiles. | Both executions pass. |
| `I16.S04.T04` | `integration-tests/whole/test_m8_invariants.py` | Check no false-safe, trust limits, ordering, bounded latency and final consistency. | Invariant suite passes. |
| `I16.S04.T05` | `tools/evidence/build_aer.py` | Build a signed after-event record from journals, traces, metrics, configs and artifact digests. | AER schema/signature tests pass. |
| `I16.S04.T06` | `integration-tests/whole/test_m8_aer.py` | Verify the AER reconstructs decisions and references immutable evidence. | AER verification passes. |

### I16.S05 — Backup, restore and operational recovery

**Stage outcome:** Owned stores and configuration can be backed up, restored and verified without violating module ownership.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I16.S05.T01` | `tools/backup/backup_owned_stores.py` | Create per-module consistent backups with manifest and digests. | Backup unit/integration tests pass. |
| `I16.S05.T02` | `tools/backup/restore_owned_stores.py` | Restore per-module data with version and compatibility validation. | Restore and negative tests pass. |
| `I16.S05.T03` | `integration-tests/recovery/test_backup_restore.py` | Compare pre-backup and post-restore journal, projections and source cursors. | End-to-end restore test passes. |
| `I16.S05.T04` | `integration-tests/recovery/test_projection_rebuild.py` | Rebuild all derived projections solely from authoritative journals/contracts. | Projection equivalence passes. |
| `I16.S05.T05` | `docs/runbooks/backup-restore.md` | Document backup, verification, restore, rollback and evidence retention. | Runbook commands pass in disposable environment. |
| `I16.S05.T06` | `docs/runbooks/whole-solution-recovery.md` | Document diagnosis and recovery for every M8 injected failure. | Runbook scenario rehearsal passes. |

### I16 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs every cumulative suite with deterministic seeds recorded.
- `make test-chaos` passes process crash, disk-full, queue saturation, clock skew, poison message, artifact loss and channel partition cases.
- `make test-whole SCENARIO=whole-solution-m8 PROFILES=compact,isolated` passes repeatedly with equivalent authoritative outcomes.
- `make test-offline PROFILE=offline-field` proves continued local monitoring, bounded storage and safe synchronization.
- All inbox, outbox and cursor crash-matrix points pass; no case is hidden by retrying the test.
- Backup/restore and projection rebuild reproduce authoritative state and expose any unsupported version rather than coercing it.
- The signed AER validates and permits an independent reviewer to trace each incident decision to inputs, contracts, configuration and software digests.
- No test is accepted as green after flaky rerun, quarantining or expected-failure conversion.

**Mandatory evidence:**

- Full chaos matrix with seeds and outcomes
- Compact/isolated M8 journals and semantic diff
- Offline disconnection/reconciliation report
- Backup/restore and projection-rebuild digest comparison
- Signed M8 after-event record
- Zero-flake cumulative test report

**Completion rule:** `I16` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I17 — Security, privacy, accessibility and supply-chain hardening

**Increment:** Make security, data governance, accessible operation and verifiable release provenance release-blocking.

**Entry condition:** `I16` is complete and the signed M8 whole-solution scenario is reproducibly green.

### I17.S01 — Secure bootstrap, identity and authorization

**Stage outcome:** Administrative access and module identity fail closed from first boot through steady state.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I17.S01.T01` | `modules/api/src/security/bootstrap.py` | Implement one-time secure admin bootstrap with expiry, rotation and audit. | Bootstrap positive/negative tests pass. |
| `I17.S01.T02` | `modules/api/src/security/auth_provider.py` | Implement configurable OIDC/local authentication abstraction with secure defaults. | Provider contract and failure tests pass. |
| `I17.S01.T03` | `modules/api/src/security/authorization.py` | Implement explicit role/capability policy for reads, commands, evidence and administration. | Authorization matrix tests pass. |
| `I17.S01.T04` | `sdk/python/sentinel_edge_transport/peer_identity.py` | Bind isolated transport identities to allowed module roles and socket credentials. | Peer spoofing tests pass. |
| `I17.S01.T05` | `modules/api/src/security/replay_guard.py` | Reject replayed or expired privileged commands. | Nonce/window/property tests pass. |
| `I17.S01.T06` | `integration-tests/security/test_authz_matrix.py` | Exercise anonymous, viewer, operator, reviewer and administrator permissions. | All deny/allow cells match policy. |
| `I17.S01.T07` | `integration-tests/security/test_secure_first_boot.py` | Prove default installation has no reusable default credential or open admin path. | First-boot security test passes. |

### I17.S02 — Privacy inventory, minimization and retention

**Stage outcome:** Personal and sensitive data are declared, minimized, purpose-limited, retained and deleted consistently.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I17.S02.T01` | `docs/governance/data-inventory.yaml` | Inventory fields, purpose, sensitivity, owner, retention and lawful/operational basis. | Inventory schema and completeness checks pass. |
| `I17.S02.T02` | `tools/privacy/validate_data_inventory.py` | Fail CI when contract fields lack inventory classification or owner. | Validator unit and repository scan pass. |
| `I17.S02.T03` | `modules/collector/src/privacy/minimizer.py` | Remove or transform disallowed metadata before durable acquisition. | Golden minimization tests pass. |
| `I17.S02.T04` | `modules/analyzer/src/privacy/media_redaction.py` | Apply configured face, plate, voice or metadata redaction before retained analysis artifacts. | Redaction quality and fail-closed tests pass. |
| `I17.S02.T05` | `modules/collector/src/retention/enforcer.py` | Enforce source-specific raw-data retention and legal-hold exceptions. | Clock/property and audit tests pass. |
| `I17.S02.T06` | `modules/analyzer/src/retention/enforcer.py` | Enforce derived-artifact retention without deleting incident-required provenance. | Retention/dependency tests pass. |
| `I17.S02.T07` | `integration-tests/privacy/test_end_to_end_deletion.py` | Verify deletion/withdrawal propagates to permitted stores and leaves required audit tombstones. | End-to-end privacy test passes. |
| `I17.S02.T08` | `integration-tests/privacy/test_data_minimization.py` | Prove forbidden metadata never reaches downstream contracts or evidence bundles. | Cross-module minimization test passes. |

### I17.S03 — Untrusted content and API abuse resistance

**Stage outcome:** Malformed media, prompts, documents, payloads and client behavior cannot escape declared resource or trust boundaries.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I17.S03.T01` | `fixtures/security/malicious-corpus/manifest.yaml` | Catalog decompression bombs, parser edge cases, prompt injection, polyglots and malformed metadata. | Corpus integrity validation passes. |
| `I17.S03.T02` | `modules/analyzer/src/security/untrusted_content.py` | Treat extracted text and metadata strictly as evidence, never executable instructions. | Injection and taint tests pass. |
| `I17.S03.T03` | `modules/runtime/src/security/workload_limits.py` | Enforce time, memory, output, artifact and recursion limits per workload. | Resource exhaustion tests pass. |
| `I17.S03.T04` | `modules/api/src/security/request_limits.py` | Enforce body, upload, query, subscription and command rate limits. | Boundary and concurrency tests pass. |
| `I17.S03.T05` | `integration-tests/security/test_malicious_corpus.py` | Run all parsers and analysis paths against the malicious corpus. | No crash, escape or trust elevation. |
| `I17.S03.T06` | `integration-tests/security/test_api_abuse.py` | Test auth bypass, enumeration, oversized payload, slow client and subscription abuse. | Abuse suite passes. |
| `I17.S03.T07` | `integration-tests/security/test_secret_isolation.py` | Prove secrets are not emitted in logs, traces, errors, AERs or client projections. | Repository and runtime scans pass. |

### I17.S04 — Accessible and safety-critical user journeys

**Stage outcome:** Primary web and mobile workflows remain operable with assistive technology, keyboard-only use and degraded connectivity.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I17.S04.T01` | `docs/accessibility/test-plan.md` | Define WCAG-oriented journeys, supported assistive modes, evidence and release thresholds. | Documentation/schema checks pass. |
| `I17.S04.T02` | `apps/web/src/styles/safety-states.css` | Define non-color-only focus, severity, degraded, unknown and stale visual semantics. | Contrast and visual-state tests pass. |
| `I17.S04.T03` | `modules/client-shared/src/accessibility/textAlternatives.ts` | Generate concise accessible alternatives for evidence, confidence and system health. | Semantic unit tests pass. |
| `I17.S04.T04` | `integration-tests/accessibility/test_web_primary_journey.py` | Test keyboard, focus, landmarks, names, live updates and offline status. | Automated accessibility journey passes. |
| `I17.S04.T05` | `integration-tests/accessibility/test_mobile_primary_journey.py` | Test screen-reader labels, target size, ordering and offline actions. | Mobile accessibility journey passes. |
| `I17.S04.T06` | `integration-tests/accessibility/test_no_color_only_meaning.py` | Verify all hazard, trust and health states have textual/iconographic alternatives. | Cross-client test passes. |
| `I17.S04.T07` | `docs/accessibility/manual-evidence.md` | Record required manual screen-reader, zoom, motion and field-usability checks. | Evidence template completeness passes. |

### I17.S05 — SBOM, provenance and reproducible release inputs

**Stage outcome:** Every release input and generated artifact is inventoried, signed and reproducible.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I17.S05.T01` | `tools/supply_chain/generate_sbom.py` | Generate CycloneDX SBOMs for Python, JavaScript, containers, models and plugins. | SBOM schema and completeness tests pass. |
| `I17.S05.T02` | `provenance/release-bill.schema.json` | Define source commit, toolchain, contracts, models, plugins, fixtures, licenses and evidence digests. | Schema tests pass. |
| `I17.S05.T03` | `tools/supply_chain/build_release_bill.py` | Assemble a deterministic release bill from verified repository artifacts. | Determinism and missing-input tests pass. |
| `I17.S05.T04` | `tools/supply_chain/verify_release.py` | Verify signatures, checksums, SBOM, licenses, schemas, model cards and test evidence. | Positive/tamper tests pass. |
| `I17.S05.T05` | `integration-tests/supply_chain/test_reproducible_build.py` | Build twice in clean environments and compare declared deterministic artifacts. | Reproducibility thresholds pass. |
| `I17.S05.T06` | `integration-tests/supply_chain/test_generated_artifact_freshness.py` | Fail when generated clients, schemas, docs or manifests are stale. | Freshness test passes. |
| `I17.S05.T07` | `docs/runbooks/security-response.md` | Document credential, plugin, source, model and supply-chain incident response. | Runbook rehearsal/checks pass. |

### I17 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- `make ci` runs the complete cumulative suite plus security, privacy, accessibility and supply-chain gates.
- `make test-security` passes secure bootstrap, authorization, peer identity, malicious corpus, API abuse, replay and secret-isolation suites.
- `make test-privacy` proves inventory completeness, minimization, retention, consent withdrawal and deletion behavior.
- `make test-accessibility` passes automated primary journeys; required manual evidence is current and signed off.
- `make test-supply-chain` generates valid SBOMs and release bill, verifies licenses/signatures and reproduces deterministic artifacts.
- Static and dynamic scanners report no unresolved critical or high-severity issue; waivers at these severities are prohibited.
- Privacy or accessibility failure blocks release exactly like a functional test failure.
- All prior hazard, source, deployment and M8 tests remain green under hardened defaults.

**Mandatory evidence:**

- Authorization decision matrix
- Privacy inventory, minimization and deletion report
- Malicious-corpus/API-abuse results
- Automated and manual accessibility evidence
- CycloneDX SBOM set and signed release bill
- Reproducible-build comparison
- Zero critical/high security finding report

**Completion rule:** `I17` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## I18 — Arm optimization, hardware qualification and release candidate

**Increment:** Qualify Sentinel Edge on declared Arm hardware, prove performance and quality envelopes, and produce the auditable release.

**Entry condition:** `I17` is complete with no unresolved release-blocking security, privacy, accessibility or provenance issue.

### I18.S01 — Arm target profile and qualification protocol

**Stage outcome:** The exact hardware, OS, toolchain, power mode and quality gates are declared before optimization.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I18.S01.T01` | `provenance/arm/target-profile.yaml` | Declare Arm CPU, architecture, cores, memory, storage, accelerator, OS, kernel, power and thermal settings. | Profile schema and hardware match checks pass. |
| `I18.S01.T02` | `provenance/arm/qualification-protocol.md` | Define warmup, sample count, timing, energy, thermal, quality, abstention and repeatability rules. | Protocol lint and completeness checks pass. |
| `I18.S01.T03` | `provenance/arm/quality-gates.yaml` | Declare hazard/workload accuracy, false-positive, abstention and latency acceptance thresholds. | Gate schema and traceability tests pass. |
| `I18.S01.T04` | `tools/arm/check_environment.py` | Verify hardware identity, governor, thermals, memory, dependencies and forbidden background load. | Environment checker positive/negative tests pass. |
| `I18.S01.T05` | `tools/arm/capture_environment.py` | Capture immutable qualification environment evidence and digests. | Capture determinism and schema tests pass. |
| `I18.S01.T06` | `integration-tests/arm/test_target_profile.py` | Prove qualification refuses mismatched or uncontrolled environments. | Arm profile tests pass. |

### I18.S02 — Measured Arm optimization

**Stage outcome:** Optimize only measured bottlenecks while preserving contracts, quality and deterministic fallback behavior.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I18.S02.T01` | `modules/runtime/config/arm/thread-budget.yaml` | Define process/workload thread and affinity budgets for the target. | Budget validation and oversubscription tests pass. |
| `I18.S02.T02` | `modules/runtime/src/memory/residency.py` | Implement bounded model residency, eviction and warmup accounting. | Memory pressure and determinism tests pass. |
| `I18.S02.T03` | `modules/runtime/src/pipeline/batching.py` | Implement deadline-aware bounded batching where quality-neutral. | Latency/throughput property tests pass. |
| `I18.S02.T04` | `modules/collector/src/channels/zero_copy.py` | Use bounded shared buffers for eligible local sensor paths with safe fallback. | Correctness, lifetime and fallback tests pass. |
| `I18.S02.T05` | `modules/analyzer/src/media/preprocessing_arm.py` | Add profiled Arm-friendly preprocessing with identical canonical outputs. | Golden equivalence and quality tests pass. |
| `I18.S02.T06` | `integration-tests/performance/test_arm_resource_envelope.py` | Measure CPU, memory, queue, thermal and deadline behavior under M8 load. | Declared envelope passes. |
| `I18.S02.T07` | `integration-tests/performance/test_optimization_equivalence.py` | Compare optimized and reference outputs across the canonical corpus. | Semantic and quality equivalence passes. |

### I18.S03 — Hardware-in-the-loop and benchmark execution

**Stage outcome:** Real camera/IMU inputs and the full benchmark execute reproducibly on the declared Arm target.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I18.S03.T01` | `integration-tests/hil/camera_imu_rig.yaml` | Describe devices, calibration, timing, fixtures and expected failure modes. | HIL rig schema and preflight pass. |
| `I18.S03.T02` | `integration-tests/hil/test_camera_imu_slice.py` | Run physical camera/IMU wildfire and seismic paths on target hardware. | HIL correctness and latency tests pass. |
| `I18.S03.T03` | `benchmarks/arm/m8-benchmark.yaml` | Define workload mix, scenario, repetitions, metrics and acceptance gates. | Benchmark definition validates. |
| `I18.S03.T04` | `tools/arm/run_benchmark.py` | Run controlled repetitions and emit raw, summary and environment-linked results. | Runner unit and dry-run tests pass. |
| `I18.S03.T05` | `tools/arm/build_benchmark_report.py` | Build human- and machine-readable performance/quality report with uncertainty. | Report schema and calculation tests pass. |
| `I18.S03.T06` | `integration-tests/arm/test_benchmark_claims.py` | Verify every performance claim is supported by captured raw evidence. | Claim-to-evidence test passes. |
| `I18.S03.T07` | `docs/benchmarks/arm-results.md` | Document target, protocol, results, limitations and reproducible commands. | Docs and evidence-link validation pass. |

### I18.S04 — Deployment, demo and operator documentation

**Stage outcome:** A reviewer or operator can install, run, inspect and recover the release without undocumented steps.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I18.S04.T01` | `docs/architecture/system-overview.md` | Publish final module boundaries, contracts, profiles, flows and ownership. | Architecture diagrams and links validate. |
| `I18.S04.T02` | `docs/deployment/arm-install.md` | Document verified clean installation for the target Arm platform. | Install commands pass on clean target. |
| `I18.S04.T03` | `docs/deployment/configuration-reference.md` | Document every supported profile, setting, default, secret and incompatibility. | Config-doc coverage test passes. |
| `I18.S04.T04` | `docs/operator/incident-workflows.md` | Document review, acknowledgement, source health, evidence and recovery workflows. | Workflow documentation tests pass. |
| `I18.S04.T05` | `docs/demo/hackathon-demo.md` | Define deterministic live/offline demo, fallback recordings and evidence links. | Demo rehearsal passes twice from clean state. |
| `I18.S04.T06` | `docs/claims/claims-register.yaml` | List every product, quality, performance, privacy and limitation claim with evidence. | Claim register validator passes. |
| `I18.S04.T07` | `README.md` | Provide final project purpose, supported scope, quick start, architecture and evidence navigation. | README commands and links pass. |

### I18.S05 — Release candidate assembly and final acceptance

**Stage outcome:** The exact tested artifacts are assembled, signed, installed cleanly and accepted against milestones M1–M8.

| Task | Primary file | Atomic modification | Targeted verification |
|---|---|---|---|
| `I18.S05.T01` | `release/release-candidate.yaml` | Pin source revision, contracts, plugins, models, images, docs and evidence artifacts. | Release candidate schema and digest checks pass. |
| `I18.S05.T02` | `tools/release/build_release.py` | Build the immutable distributable bundle from pinned verified inputs. | Build determinism and missing-input tests pass. |
| `I18.S05.T03` | `tools/release/verify_release.py` | Verify signatures, release bill, SBOMs, tests, claims and compatibility before install. | Tamper and completeness tests pass. |
| `I18.S05.T04` | `integration-tests/release/test_clean_install.py` | Install on a clean Arm target and execute smoke plus rollback tests. | Clean-install test passes. |
| `I18.S05.T05` | `integration-tests/release/test_final_acceptance.py` | Execute milestone acceptance M1–M8 and compare required evidence. | Final acceptance suite passes. |
| `I18.S05.T06` | `release/acceptance-record.md` | Record approvers, commands, hashes, results, limitations and release decision. | Record completeness/signature check passes. |
| `I18.S05.T07` | `release/CHANGELOG.md` | Document delivered capabilities, migrations, known limitations and rollback path. | Changelog/release-version checks pass. |

### I18 end-of-iteration comprehensive gate

Run the complete standard gate plus these iteration-specific proofs:

- From a clean checkout, run the exact standard gate sequence in §5 with no omitted suite and no stale generated artifact.
- `make test-arm TARGET=declared` passes hardware identity, HIL, resource envelope, thermal, quality and repeatability gates.
- `make benchmark-arm BENCHMARK=m8-benchmark` completes the declared repetitions and produces evidence-linked results.
- `make test-whole SCENARIO=whole-solution-m8 PROFILES=compact,isolated,offline-field` passes with authoritative semantic equivalence where applicable.
- `make test-release` verifies the immutable release candidate, performs clean Arm installation, executes rollback and runs final M1–M8 acceptance.
- Every entry in the claims register resolves to current signed evidence; unsupported or overstated claims block release.
- The distributable bundle contains no development secret, unapproved model, incompatible plugin, stale schema, missing license or unverified generated artifact.
- All tests pass on the exact release candidate—not merely on an earlier workspace build—with zero unexpected skip, xfail, retry or flake.
- The iteration and project remain incomplete until the signed acceptance record is produced after all preceding checks pass.

**Mandatory evidence:**

- Captured Arm environment and target-profile match
- Raw benchmark runs plus performance/quality report
- HIL camera/IMU evidence
- Complete clean-checkout CI transcript
- Final M1–M8 acceptance report
- Signed SBOMs, release bill, claims register and release candidate
- Clean-install and rollback transcript
- Signed release acceptance record

**Completion rule:** `I18` remains `in-progress` until every mandatory command and proof above passes with current artifact hashes and zero unexpected skips, expected failures, flaky reruns or collection errors.

## 9. Persistent test activation matrix

Once a suite is activated, it remains mandatory in every later iteration. A later optimization, profile, plugin or hazard pack may add tests but may not remove, mute, quarantine or weaken an existing assertion without an approved architecture decision and an equivalent or stronger replacement.

| Suite | First mandatory iteration | Permanent scope | Release-blocking failure examples |
|---|---:|---|---|
| Formatting, lint and static analysis | I00 | Entire repository | Parse error, type error, stale lint waiver |
| Architecture and ownership | I00 | Imports, stores, contracts, composition roots | Cross-module implementation import, shared writable store, hidden composition |
| Unit and property tests | I00 | Every module and SDK | Failed invariant, nondeterminism, uncaught boundary case |
| Contract schemas/examples | I01 | JSON Schema, AsyncAPI, OpenAPI, CloudEvents profile | Invalid example, incompatible schema, undocumented field |
| Generated artifact freshness | I01 | Models, clients, docs and manifests | Generated diff after clean regeneration |
| Plugin conformance | I01 | Source, workload, policy, projection and client plugins | Permission excess, incompatible version, resource overrun |
| Standalone module black-box tests | I02 | All six module packages | Module requires another implementation to start or test |
| Collector component tests | I03 | Ingress, quarantine, replay, backpressure | Lost accepted input, silent malformed input, unbounded queue |
| Runtime component/performance tests | I04 | Registry, scheduler, workloads, probes | Unqualified execution, deadline/resource breach, hidden fallback |
| Incident authority tests | I05 | Journal, policy, effects, review | Invalid transition, duplicate effect, false-safe projection |
| API consumer/provider tests | I06 | REST, commands, SSE/WS, generated clients | Schema/semantic mismatch, authorization bypass, resume gap hidden |
| Client accessibility/offline tests | I07 | Shared, web and mobile | Inaccessible critical state, lost queued command, color-only meaning |
| Physical wildfire vertical slice | I08 | Camera/IMU hot path | Incorrect incident, missing review path, unbounded Tier-A latency |
| Analyzer trust/lineage tests | I09 | Claims, provenance and calibration | Unsupported trust increase, broken lineage, source dependence ignored |
| External multimodal vertical slice | I10 | Rights-gated image/audio/video path | Rights bypass, parser escape, external evidence becomes authority |
| Flood pack suite | I11 | Flood collection through UI | Missing coverage treated as safe, unqualified site model |
| Earthquake pack suite | I12 | Post-onset seismic path | Predictive claim, missed Tier-A deadline, clock quality ignored |
| Landslide pack suite | I13 | Site-qualified saturation/movement path | Susceptibility alone confirms incident, silent adaptation |
| Source connector conformance | I14 | All governed source plugins | Network-dependent judge, rights violation, stale source hidden |
| Isolated transport/profile tests | I15 | UDS framing, artifacts, supervision | Mixed pack activation, peer spoof, compact/isolated semantic drift |
| Chaos, crash matrices and recovery | I16 | Inbox/outbox/cursors, offline, backup/restore | Lost journal event, irrecoverable hidden gap, flaky recovery |
| Security/privacy/accessibility/supply chain | I17 | Complete solution and release inputs | Critical/high finding, privacy leak, inaccessible primary journey |
| Arm HIL/performance/release acceptance | I18 | Exact release candidate on declared target | Unsupported claim, hardware mismatch, quality or resource gate failure |

### 9.1 Required execution order

Run suites in the following order so cheap deterministic failures stop the pipeline before expensive integration and hardware work:

1. Repository cleanliness, formatting, lint and type checks.
2. Architecture and ownership boundary checks.
3. Unit, property, mutation-target and deterministic replay tests.
4. Plugin conformance, permissions and resource-budget tests.
5. Schema, compatibility, examples and generated-artifact freshness.
6. Module component and standalone black-box tests.
7. Consumer/provider and mandatory pairwise contract tests.
8. Activated hazard/source pack conformance tests.
9. Vertical slices and profile equivalence.
10. Whole-solution, chaos, crash-matrix, offline and recovery tests.
11. Security, privacy and accessibility tests.
12. Arm HIL, resource, quality, thermal and benchmark tests.
13. SBOM, provenance, reproducibility, documentation and release verification.

### 9.2 Test-result integrity rules

- A retry does not convert a failure into a pass. Any non-identical repeated result opens a flakiness defect.
- An unexpected skip, deselection, collection error, timeout or expected failure is a failed gate.
- Test evidence must identify source revision, dependency lock hashes, profile, seed, fixtures, contracts, active plugins, model digests and hardware where applicable.
- Golden files may be updated only with an explicit behavioral explanation and reviewer approval; regeneration alone is insufficient.
- Performance gates compare against declared absolute thresholds and a versioned baseline. A faster but lower-quality result fails.
- Network access is denied in deterministic judges unless the test explicitly validates a connector in an isolated controlled environment.
- The final release gate reruns against the exact immutable candidate bundle.

## 10. Final milestone acceptance mapping

| Milestone | Acceptance statement | Primary proving iterations | Final evidence required |
|---|---|---|---|
| **M1 — Module independence** | Every module builds, starts and passes standalone black-box tests using only contracts, fixtures and test doubles. | I02–I18 | Six standalone reports; architecture-boundary report; owned-store inventory |
| **M2 — Contract integrity** | All schemas, examples, current/N-1 compatibility checks and generated clients pass. | I01, I06, I15, I18 | Contract catalog; compatibility matrix; clean regeneration diff |
| **M3 — Plugin safety** | Every selected plugin passes conformance, permissions, compatibility and resource-budget tests. | I01, I08–I15, I17 | Plugin conformance matrix; signed manifests; quarantine/rollback evidence |
| **M4 — Pairwise integration** | Every declared boundary has at least one real producer/consumer verification. | I03–I10, I15 | Reports for 01→02, 01→03, 01→04, 02↔03, 02→04, 03→04, 04↔05 and 05↔06 |
| **M5 — Vertical slices** | The physical hot path and rights-gated external evidence path pass end to end. | I08, I10 and regressions | Signed scenarios, journals, projections, client snapshots and latency evidence |
| **M6 — Whole solution** | The simultaneous scenario passes without Tier-A regression or false state authority. | I16, I18 | Compact/isolated/offline M8 results; invariant report; signed AER |
| **M7 — Recovery** | Worker/module restart, inbox/outbox replay, cursor resume, backup and projection rebuild pass. | I15–I16 | Crash matrices; recovery transcript; backup/restore digest comparison |
| **M8 — Non-functional** | Benchmark fairness, security, privacy, accessibility, provenance and rights gates pass. | I14, I17, I18 | Arm report; security/privacy/accessibility evidence; SBOM; release bill; rights catalog |

## 11. Release-blocking defect policy

### 11.1 Defect classes

| Class | Examples | Iteration disposition |
|---|---|---|
| **Safety/state authority** | False-safe state, external source resolves incident, missing data interpreted as normal, invalid lifecycle transition | Stop immediately; iteration remains incomplete; add regression before fix is accepted |
| **Data loss/consistency** | Accepted observation lost, journal divergence, duplicate irreversible effect, cursor gap hidden | Stop immediately; preserve failing artifacts; exercise adjacent crash points |
| **Security/privacy/rights** | Authentication bypass, secret exposure, unconsented retention, rights-policy bypass, parser escape | Stop immediately; rotate affected secrets/data where required; rerun full security/privacy suite |
| **Contract/compatibility** | Breaking current/N-1 change, generated client mismatch, mixed hazard pack | Reject change or ship versioned migration and compatibility evidence |
| **Accessibility** | Primary workflow unusable by keyboard/screen reader, critical meaning conveyed only by color | Release-blocking; fix and rerun full primary journeys |
| **Performance/resource** | Tier-A deadline missed, memory/thermal limit exceeded, starvation, quality regression | Release-blocking on declared target/profile; optimize or revise an evidence-backed requirement |
| **Reliability/flakiness** | Non-reproducible result, pass after retry, timing-sensitive hidden race | Treat as failure; isolate cause and make test deterministic before proceeding |
| **Documentation/provenance** | Unreproducible command, missing license, stale schema, unsupported claim | Release-blocking because the tested artifact cannot be independently verified |

### 11.2 Fix acceptance

A defect is closed only when:

1. The smallest deterministic reproducer is committed.
2. A regression test fails on the faulty revision and passes on the fix.
3. Adjacent invariants and failure points are tested, not only the observed symptom.
4. The owning module suite passes.
5. Every affected pairwise, vertical, whole-solution and non-functional suite passes.
6. Evidence and documentation are updated.
7. The iteration gate is rerun from its first step; partial previous results are not reused when inputs changed.

## 12. Iteration execution discipline

### 12.1 Status transitions

`planned → in-progress → implementation-complete → gate-running → blocked|complete`

- `implementation-complete` means all tasks and stage checks are done; it is not iteration completion.
- `gate-running` requires a clean worktree or a recorded candidate digest.
- Any failed, skipped or flaky gate moves the iteration to `blocked`.
- Only a fully passing comprehensive gate may move the iteration to `complete`.
- Work on the next iteration may be explored on a separate branch, but it must not be merged into the release line before the current iteration is complete.

### 12.2 Per-task workflow

1. Confirm the task has one primary file and one observable behavioral intent.
2. Add or update the narrowest failing test first whenever behavior changes.
3. Modify only the named primary file; open a new task for another file.
4. Run targeted verification and record the command/result in the iteration evidence ledger.
5. Review boundary, security, privacy, performance and documentation impact.
6. Commit with task ID and artifact hashes.

### 12.3 Per-stage workflow

1. Confirm every task is complete and independently reviewed.
2. Run all touched-module suites.
3. Run affected consumer/provider and pairwise tests.
4. Validate contracts, fixtures, generated outputs and documentation.
5. Demonstrate the functional stage outcome through an executable scenario or component test.
6. Mark the stage complete only when no open defect is associated with it.

### 12.4 Per-iteration workflow

1. Freeze the candidate revision, locks, fixtures, active packs, models and configuration.
2. Build from a clean environment.
3. Execute the standard gate in order plus the iteration-specific gate.
4. Preserve raw logs, reports, traces, journals, metrics, snapshots and digests.
5. Investigate every anomaly; do not normalize deviations as expected behavior without a reviewed requirement change.
6. Rerun the complete gate after any code, configuration, fixture, model, dependency or environment change.
7. Sign the iteration acceptance record and update capability states only after full success.

### 12.5 Suggested evidence ledger

Maintain `provenance/iterations/<iteration>/acceptance.yaml` with:

- iteration and candidate revision;
- task and stage completion states;
- command, start/end time and exit code for every gate;
- environment, profile, seed and hardware identifiers;
- dependency, schema, plugin, model and fixture digests;
- test counts including passed, failed, skipped, xfailed and flaky;
- links/digests for reports, journals, traces, metrics and screenshots;
- open limitations and explicit non-claims;
- reviewer and acceptance signatures.

## 13. Source-document traceability

This plan is derived from the Sentinel Edge v0.13.0 modular document set and keeps its architectural invariants as delivery gates. The primary source documents are:

- `sentinel-edge-system-functional-architecture-v0.13.0.md`
- `sentinel-edge-system-technical-architecture-specifications-v0.13.0.md`
- `sentinel-edge-module-01-streaming-source-collector-functional-v0.13.0.md`
- `sentinel-edge-module-01-streaming-source-collector-technical-v0.13.0.md`
- `sentinel-edge-module-02-analyzer-model-event-generator-functional-v0.13.0.md`
- `sentinel-edge-module-02-analyzer-model-event-generator-technical-v0.13.0.md`
- `sentinel-edge-module-03-model-workload-runtime-functional-v0.13.0.md`
- `sentinel-edge-module-03-model-workload-runtime-technical-v0.13.0.md`
- `sentinel-edge-module-04-incident-event-engine-functional-v0.13.0.md`
- `sentinel-edge-module-04-incident-event-engine-technical-v0.13.0.md`
- `sentinel-edge-module-05-rest-api-integration-gateway-functional-v0.13.0.md`
- `sentinel-edge-module-05-rest-api-integration-gateway-technical-v0.13.0.md`
- `sentinel-edge-module-06-web-mobile-clients-functional-v0.13.0.md`
- `sentinel-edge-module-06-web-mobile-clients-technical-v0.13.0.md`

### 13.1 Non-negotiable inherited invariants

- The Incident & Event Engine is the sole incident lifecycle authority and writer.
- Modules own their stores and communicate through versioned contracts, never cross-module implementation imports.
- Missing, stale, unhealthy or incomplete data is explicit and is never interpreted as normal or safe.
- External or low-trust evidence may update context and confidence but cannot independently verify, resolve or mark an incident safe.
- All models, workloads and plugins are qualified for their declared profile before they can affect benchmark or production decisions.
- Compact, isolated and offline-field deployments preserve authoritative domain semantics.
- Physical and external-evidence vertical slices, the simultaneous whole-solution scenario and the M1–M8 acceptance set are permanent release gates.

## 14. Final completion condition

The project is build-complete only when `I00` through `I18` are each marked `complete`, every persistent test suite is green against the exact immutable release candidate, all M1–M8 evidence is present and signed, and no release-blocking defect, unexpected skip, flaky rerun, stale artifact or unsupported claim remains.

Until that condition is true, the project status is **not complete**.
