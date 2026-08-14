# Changelog

## Unreleased — 2026-08-14 hackathon emulator hardening

- Made local setup reproducible from a clean checkout with a standard site-packages `.pth`, a hash-pinned Judge/test lock, and an explicit compatible-preprovisioned fallback that is disabled by final submission preflight.
- Pinned the Arm64 Docker base by OCI digest and generated a full hash-locked, binary-only AArch64 dependency set, including publisher-index wheel identities for ONNX Runtime 1.28.0 and its numerical/runtime dependencies.
- Added real AArch64 ONNX Runtime known-answer execution through `CPUExecutionProvider`, provider-fallback rejection, installed distribution `RECORD` fingerprinting, native-library hashing, and model size/digest binding.
- Extended B0/B1/O1 evidence with total service/queue-delay accounting, heavy-workload invocation/duty-cycle metrics, explicit simulated thermal/power/resource labels, and an emulator-measured scheduler control-plane overhead microbenchmark.
- Hardened final candidate admission so stale Arm64 benchmark evidence lacking the new runtime and scheduler/workload instrumentation cannot satisfy the frozen release.
- Fixed the public Judge source export allowlist so the package now includes Docker/Arm64 build inputs, hash-pinned dependency locks, schemas, package metadata, security/contribution guidance, and the hackathon work log required to reproduce and audit the submission.
- Hardened clean-checkout setup against stale editable installs: the active checkout is prepended through a deterministic `.pth`, setup verifies the resolved `sentinel_edge` module lives under the current checkout, and legacy checkout `.pth` files are removed.
- Isolated admitted-candidate Judge-package smoke verification in a temporary virtual environment and added an explicit active-checkout import guard; `python scripts/dev.py package` automatically runs the fresh-copy verification once a candidate is release-admitted.
- Made the strict `test-all` lane safely resumable across interrupted runs: reusable batch receipts are accepted only when source-tree, setup/runtime fingerprint, test-path set, batch signature, collection count, and no-skip/no-xfail/no-failure conditions all match.
- Fixed the release-export dirty-worktree regression test so it creates its own temporary untracked probe instead of depending on the developer repository already being dirty.

## 0.21.0 — 2026-08-03

- Added a closed qualification vocabulary and claim ceiling over the weakest effective evidence state.
- Added explicit qualification validity windows, expiry consequences and reconstructed-evidence limitations.
- Added platform runtime-envelope binding and Raspberry Pi 5 vector-claim rejection.
- Expanded benchmark-host observations and idle/noise qualification.
- Added cold/session initialization and branch/shape/output known-answer runtime gates.
- Bound the new reports into release qualification and candidate admission.

## 0.20.0 — 2026-08-03

- Added a bounded ONNX protobuf inspector with exact graph/operator fingerprints, allocation contracts and malformed-model rejection.
- Added read-only, package-local model admission with exact file identities, runtime/provider/fallback and known-issue binding.
- Added Component-3 execution-boundary scanning that rejects Python/custom/plugin/runtime-extension payloads.
- Added signed IMU and camera signal-chain profiles covering rates, anti-aliasing, timestamps, gaps, FIFO overflow, clipping, saturation, quantization and model compatibility.
- Added signed site commissioning that binds site, sensor, profile, configuration, calibration, mounting, datum/baseline and model identity.
- Bound model-package and signal-chain reports into release-candidate admission while preserving development-only status.
- Moved 19 directly exercised requirements to `IMPLEMENTED`, for 246 implemented requirements and 93 implemented H0 requirements.
- Added 12 focused v0.20 tests; the complete development suite contains 225 tests.

## 0.19.0 — 2026-08-03

- Added current/history-separated under-voltage, frequency-cap, throttling and temperature observations plus authenticated Mission Control power-health endpoints.
- Added deterministic `DEGRADED_POWER` and recovery-hysteresis state transitions.
- Added benchmark invalidation for current power threats, swap use, excessive major faults and memory PSI, with retained reason codes.
- Added physical-energy and non-energy-proxy contracts with method, sampling, idle subtraction, uncertainty, instrument, complete-node scope and fixed-quality-target validation.
- Added signed, versioned, expiring runtime-known-issue registries and exact, evidence-backed, owned, expiring, rollback-ready exceptions.
- Added release-candidate and provenance bindings for power/energy and runtime-known-issue reports.
- Removed seven Pydantic schema-field shadow warnings while preserving external JSON `schema` keys.
- Moved 10 directly exercised requirements to `IMPLEMENTED`, for 227 implemented requirements and 82 implemented H0 requirements.
- Expanded the development suite from 200 to 213 passing tests.

## 0.18.0 — 2026-08-03

- Added Ed25519-signed benchmark analysis plans that must predate confirmatory execution.
- Added exact runtime, model, configuration, fixture, host, network and target-wheelhouse identity binding.
- Added contiguous alternating B0/B1/O1 block validation and complete-pair accounting.
- Added deterministic paired percentile-bootstrap intervals, absolute values and standardized effect sizes.
- Preserved excluded benchmark records and exact invalidation reasons.
- Added strict exploratory-versus-confirmatory separation and blocked exploratory headline claims.
- Added same-network-namespace benchmark workload launch after no-egress preflight probes.
- Added Arm64 target-wheel acquisition and verification contracts without fabricating missing publisher evidence.
- Bound target-wheelhouse and benchmark-analysis reports into release-candidate admission.
- Moved six directly exercised requirements to `IMPLEMENTED`; no requirement moved to `VERIFIED`.
- Expanded the development suite from 193 to 200 passing tests.

## 0.17.0 — 2026-08-03

- Added deterministic installed-distribution wheel capture and exact lock-closure verification.
- Added hash-locked, no-index offline installation rehearsal for the complete Python runtime resolution.
- Added observed Linux network-namespace denial for DNS, TCP and deliberately misbehaving-adapter probes.
- Added signed independent-builder attestation contracts and distinct builder/host/environment enforcement.
- Added signed independent security/privacy/accessibility review packets with evidence-bearing finding lifecycle and waiver expiry.
- Added release-credential profile checks for external private keys, purpose separation, rotation and development-credential absence.
- Bound wheelhouse, network isolation, independent build and release governance reports into the release-candidate identity.
- Moved `REQ-HOST-002` and `REQ-RPB-003` to `IMPLEMENTED`; no requirement moved to `VERIFIED`.

## 0.16.0 — 2026-08-03

- Added exact installed dependency locking and bound the lock, build definition, toolchain and `SOURCE_DATE_EPOCH` into provenance.
- Added paired deterministic source-bundle builds from different absolute paths and discovery orders, producing byte-identical ZIP artifacts under a fixed canonical archive contract.
- Added scoped reproducibility classes and material-difference analysis that does not normalize executable, model or configuration changes away.
- Added explicit Python-level network denial for the reproducible source-build path while retaining OS-level egress denial and offline wheel-mirror work as open.
- Added normalized OSV, GitHub Advisory, CISA KEV and vendor advisory source classes with coverage policy, known-exploitation, reachability, exploit-maturity and operational-exposure fields.
- Added incident-driven toolchain quarantine and exact denial of the July 2026 affected AsyncAPI package versions, with mandatory credential/runner review and clean rebuild evidence.
- Added host/boot trust observations for exposed bootloader, kernel, initramfs, root filesystem, firmware and hardening identities, with explicit residual privileged-host limitations.
- Added distinct boot-signing, release-signing, device-identity and backup-decryption purpose domains and kept customer-key secure boot optional outside H0/Judge.
- Added benchmark-host observation, idle/noise envelope and below-application network-isolation contracts without claiming current target evidence.
- Moved 12 directly exercised H1 requirements to `IMPLEMENTED`, for 209 implemented requirements and 69 implemented H0 requirements.
- Expanded the development suite from 178 to 185 passing tests.

## 0.15.0 — 2026-08-03

- Added one canonical typed Component-4 authority watermark carrying epoch, highest contiguous position, accepted event count, validity and failures.
- Propagated the same watermark through authenticated projections, live `resync_required` messages, deterministic After-Event Review, backup manifests, restore receipts, evidence exports and decommission receipts.
- Bound backup watermark claims to the copied incident store and added tamper tests for substituted event counts/positions.
- Added restart-safe external-recipient reconciliation attempts with bounded retries, deadlines, terminal exhaustion, transport-exception evidence and receipt-backed completion.
- Added authorized API inspection of external-recipient reconciliation history.
- Added observed network-removal evidence covering active listeners, permitted loopback endpoints, firewall default-deny, ingress/service removal and external probe outcomes.
- Moved `REQ-AJL-005` to `IMPLEMENTED`, for 197 implemented requirements and 69 implemented H0 requirements.
- Expanded the development suite from 174 to 178 passing tests.

## 0.14.0 — 2026-08-03

- Added signed audit-head checkpoints over exact contiguous Component-4 journal prefixes with chain, epoch, signer generation and verification-policy binding.
- Added explicit non-forensic wording and verification failures for truncation, prefix substitution, wrong epoch, unknown policy and invalid signatures.
- Added versioned Ed25519 public-key lifecycle with planned rotation/retirement, policy revocation and suspected/confirmed compromise semantics.
- Preserved historical checkpoint validity under the recorded policy while preventing retired/revoked keys from signing new accepted heads.
- Added source-key revocation checks so revoked identities cannot contribute new trusted evidence.
- Added principal/session/device-scoped protected local grants and purge receipts for logout, device revocation, expiry, retirement and compromise.
- Added authenticated logout and administrative device-revocation operations that disable bearer authority and purge protected cache/queued commands.
- Added bounded background-connector drain/stop receipts proving that no hidden worker remains receiving after shutdown.
- Added fail-closed decommission receipts covering connector quiescence, unresolved dispositions, pending notifications/spool work, grant purge, key retirement/revocation and network-exposure removal without claiming secure erasure.
- Bound evidence exports to the represented authority epoch and highest contiguous journal position.
- Moved 9 directly exercised requirements to `IMPLEMENTED`, for 196 implemented requirements and 69 implemented H0 requirements.
- Expanded the development suite from 164 to 174 passing tests.

## 0.13.0 — 2026-08-03

- Made artifact policy mandatory for every content-addressed write and added producer-specific policies for configurations, telemetry, claims, reviews, sanitized media and exports.
- Added cumulative source, incident, scenario/run, release-candidate and node budgets plus reference-protected garbage collection.
- Added public/Judge export scanning for credentials, private keys, reporter content, device identifiers, restricted coordinates and non-redistributable markers.
- Added governed erasure, restriction, correction and consent-withdrawal requests with immediate restriction and registered lineage across originals, derivatives, OCR/ASR, embeddings, indexes, caches, exports, grants, leases, replicas and external recipients.
- Added receipt-backed external deletion, explicit retained exceptions, unresolved-recipient reporting and minimal non-content tombstones.
- Added versioned owner/purpose-scoped secret references, process-memory-only values, bounded rotation, stale-handle invalidation, metadata-only provenance and dependent-capability degradation.
- Added repository/output secret-canary scanning and a candidate-bound privacy-closure report.
- Moved 17 directly exercised requirements to `IMPLEMENTED`, for 187 implemented requirements and 69 implemented H0 requirements.
- Expanded the development suite from 150 to 164 passing tests.

## 0.12.0 — 2026-08-02

- Added privacy-closed backup manifests containing retention, exact legal hold, secret-reference policy, tombstone journal digest/watermark, module schemas, file digests, SQLite integrity and authority convergence evidence.
- Added restore-time application of backup and newer tombstone journals before readiness so pre-deletion backups cannot resurrect deleted evidence.
- Added explicit backup retention decisions and hash-receipted expired-backup deletion, blocked by active exact backup-scoped legal holds.
- Added exact closed evidence-export ZIPs with declared-member verification, rights/lifecycle decisions, restricted metadata redaction, derivative lineage and classification inheritance.
- Added secret-prohibited and undeclared/dangling export-member rejection.
- Bound offline update verification and activation to minimum tombstone authority positions and optional exact journal digests, and prohibited updates from targeting evidence/privacy/state/backup/artifact namespaces.
- Added authenticated export API routes and backup/tombstone/export CLI operations.
- Moved 7 directly exercised requirements to `IMPLEMENTED`, for 170 implemented requirements and 68 implemented H0 requirements.
- Expanded the development suite from 141 to 150 passing tests.

## 0.11.0 — 2026-08-02

- Added append-only evidence lifecycle events and projections for available, metadata-only, redacted, expired, deleted, unavailable-at-capture, and missing-external states.
- Added explicit `retain_bytes`, `derived_only`, and `reference_only` rights modes plus deterministic rights-expiry enforcement.
- Added content-addressed byte deletion with deletion proof digests, irreversible deleted state, and restart reconstruction.
- Added claim reconciliation so expired/deleted evidence stops contributing to current support while historical links remain auditable.
- Added evidence invalidation reevaluation records that explicitly avoid automatic incident-state mutation.
- Added resource-bounded JPEG/PNG child-process parsing, signature-based MIME detection, mismatch quarantine, pixel/input/output/time/CPU/memory/fd limits, and PNG re-encoding that strips EXIF/source metadata.
- Added authenticated lifecycle, rights-expiry, parser-report, and media-parse API routes plus a `sanitize-media` CLI command.
- Moved 9 directly exercised requirements to `IMPLEMENTED`, for 163 implemented requirements and 68 implemented H0 requirements.
- Expanded the development suite from 132 to 141 passing tests.

## 0.10.0 — 2026-08-02

- Added a Component-4-owned evidence, claim, claim-link, and incident-relation graph.
- Added exact-content, perceptual-hash, origin, parentage, and explicit-proof evidence-family/independence accounting.
- Preserved source standing, media integrity, extraction confidence, freshness, rights, retention, and parser isolation as separate trust dimensions.
- Added contradiction-preserving claim links and restart-stable graph digests.
- Added rights-required retained media and prohibited face, speaker, and person re-identification.
- Added hazard-specific temporal-spatial incident identity with uncertainty, exact source-event deduplication, restart persistence, and event-storm notification suppression.
- Added exact-version corroborate, contradict, resolve, reopen, link, and merge commands with high-impact reconfirmation and durable idempotency.
- Added cross-hazard links without incident-state collapse and same-hazard merge aliases without history deletion.
- Moved 12 directly exercised requirements to `IMPLEMENTED`, for 154 implemented requirements and 68 implemented H0 requirements.
- Expanded the development suite from 118 to 132 passing tests.

## 0.9.0 — 2026-08-02

- Added versioned per-channel measurement contracts with property identity, unit, quality, uncertainty, phenomenon interval, statistic, axis, orientation/sign convention, and reference/datum.
- Added a registry that rejects structurally invalid measurements before hazard logic and strips unusable channels while preserving suspect/unknown evidence.
- Added authenticated-time policy separating UTC trust from monotonic scheduling, including display-only unauthenticated NTP, abstract authenticated-NTS policy, discontinuity epochs, source disagreement, rollback and bootstrap restrictions.
- Added RFC 7946 geometry validation, explicit axis-order and antimeridian handling, geodesic distance, uncertainty-preserving overlap, and vertical-reference compatibility.
- Added exact legacy observation migration with deterministic identities, raw-payload preservation, ambiguous-schema quarantine, worker contract handshakes, and copy-only SQLite migration rehearsal.
- Added digest-bound Component-4 authority supertype/subtype records, epoch ordinals, predecessor chain, payload hashes, contiguous watermark, orphan detection, and projection-conformance checks.
- Bound command authorization and idempotency to the canonical encoding version.
- Added authenticated API and CLI surfaces for measurement validation, time policy, geospatial proof, and schema migration.
- Moved 27 directly exercised requirements to `IMPLEMENTED`, for 142 implemented requirements and 64 implemented H0 requirements.
- Expanded the development suite from 96 to 118 passing tests.

## 0.8.0 — 2026-08-02

- Added versioned, configurable flood thresholds with explicit missing-data masks, partial/blind coverage, susceptibility separation, and deterministic predictor fallback.
- Added stateful landslide 1h/6h/24h rainfall accumulation, direct-movement versus susceptibility separation, bounded cadence recommendations, and safe public wording.
- Added a durable bounded critical-analysis spool for Component-4 outages with idempotency, item/byte/age limits, explicit rejection/exhaustion, ordered reconciliation, and no silent overwrite.
- Added critical artifact capacity reserves, read-only degradation, directory synchronization, storage-health projections, and API visibility.
- Added SQLite WAL/FULL durability evidence, online checkpointing, integrity checks, per-module backup manifests, exact hashes/table counts/watermarks, isolated restore, and reconciliation-before-readiness.
- Added batched noncritical telemetry write accounting with logical/physical bytes, write-amplification proxy, daily-budget projection, and retention estimate.
- Added Tier-A-aware maintenance coordination that defers ordinary checkpoints/backup/GC during critical windows but records forced safety actions and their consequences.
- Added storage/checkpoint/spool API operations and backup/verify/restore CLI commands.
- Moved 16 directly exercised requirements to `IMPLEMENTED`, for 115 implemented requirements and 57 implemented H0 requirements.

## 0.7.0 — 2026-08-02

- Added deterministic camera commissioning for frame-rate, jitter, capture age, sequence continuity, resolution, freeze, darkness, blur, occlusion and physical `/dev/video*` identity.
- Made camera-health evidence part of the wildfire adapter; degraded visual quality forces partial/blind coverage and abstention and cannot strengthen incident state.
- Added compact-model artifact/dataset/known-answer hashing, graph quarantine, external-data rejection, licence resolution, deterministic scoring and event-level quality guardrails.
- Added development/calibration/final-claim group-leakage detection and frozen final-claim-set enforcement.
- Added source-policy manifests and observations covering maturity, ownership, canonical location, access/account/region availability, entitlement, rights, terms/licence, support assumptions, freshness, review/expiry and failure behavior.
- Added independent source readiness states, authenticated-cache scope binding, snapshot-generation requirements and explicit `review_required` behavior.
- Extended release-candidate qualification closure with model-quality and source-readiness records.
- Expanded the development suite from 70 to 79 passing tests.

## 0.6.0 — 2026-08-02

- Added a fail-closed startup readiness barrier covering active configuration, schema compatibility, storage, clock, minimum coverage, recovery reconciliation, and runtime-profile completeness.
- Added `/ready` and fenced scenario processing when the readiness state is not `ready`.
- Added machine-readable Raspberry Pi 5 H0 host-profile observation and qualification with architecture, board, memory, CPU, PSI, cgroup v2, thermal, power/throttling, boot identity, and observed-file digests.
- Added deterministic IMU commissioning reports with sample-rate tolerance, interval jitter, maximum gap, monotonic clock, sequence-gap, unit, saturation, and physical character-device checks.
- Added runtime-profile manifests and qualification bound to exact model, runtime version, provider, input/output contract, thread policy, evidence hashes, host binding, and expiry.
- Added target benchmark-evidence validation requiring measured source class, complete B0/B1/O1 variants, a common opportunity manifest, quality guardrails, thermal validity, power validity, and a target-qualified host.
- Added explicit qualification closure to release-candidate identity; development fixtures remain non-admitted.
- Unified new qualification outputs on the existing generated capability-state vocabulary and added field-qualified, deferred, and failed states.
- Expanded the development suite from 60 to 70 passing tests.

## 0.5.0 — 2026-08-02

- Added authenticated incident projection resources with signed HMAC envelopes, ETags, stream epochs, authority watermarks, projection versions, rebuild state, lag, and committed command identities.
- Added authenticated SSE-compatible projection delivery subordinate to REST, cursor parsing, gap/epoch detection, and explicit `resync_required` recovery.
- Updated the local PWA to resume the live projection with bearer authentication and fetch the authoritative REST projection before showing continuity after a gap.
- Added minimal offline review tickets carrying issue/expiry times, base incident version, principal/trust epochs, and idempotency identity.
- Added ticket authentication, tamper rejection, cross-principal rejection, expiry/reconfirmation, stale-base rejection, and fresh gateway reauthorization before Component-4 mutation.
- Added restart-safe durable command-receipt tests and reconciliation with current projection state.
- Added SLSA provenance-shaped local build evidence with exact repository-material digests, builder policy, environment/locale/timezone, credential-output scan, and explicit provenance-only/non-hermetic limits.
- Added normalized advisory observations, exact package/version matching, visible platform/feature predicates, bounded-source completeness, conflict preservation, and subject-bound expiring VEX decisions.
- Bound SBOM, provenance, security review, and candidate inventory evidence; a changed bound review now reopens candidate verification.
- Expanded the development suite from 48 to 60 passing tests.

## 0.4.0 — 2026-08-02

- Added bearer-token authentication with explicit viewer/operator/admin roles, token-digest retention, trust epochs, structured 401/403 outcomes, and development-credential non-admission visibility.
- Removed actor, role, scope, and principal fields from public review mutation schemas.
- Added exact payload/principal/operation/target/policy authorization binding in Component 5 and independent verification in Component 4.
- Added durable principal/operation/target-scoped idempotency receipts, replay handling, cross-principal separation, and changed-payload conflict detection.
- Added API no-store headers, CSP, anti-framing, MIME-sniffing and referrer protections.
- Added a semantic local PWA shell with an explicit static cache allowlist and no persistent bearer-token storage.
- Added Ed25519-signed offline update bundles with canonical metadata, expiry, compatibility, target digest, path, rollback/replay, self-test, activation-pointer, and immutable judge/benchmark controls.
- Added CycloneDX 1.7 SBOM, direct third-party inventory, notices generation, completeness caveats, release-candidate signatures, and offline signature verification.
- Added CSPRNG bearer-token generation.
- Expanded the development suite from 36 to 48 passing tests.

## 0.3.0 — 2026-08-02

- Added content-addressed configuration bundles with schema/hash validation, deterministic self-test, bounded runtime canary, transactional activation, active/last-known-good pointers, complete actor/diff/result history, and automatic rollback.
- Added a Component-4 transactional notification outbox so accepted incident truth and notification intent commit together.
- Added stable idempotency keys, at-least-once delivery semantics, retry history, dead-letter handling, and notification-failure isolation from incident truth.
- Added acknowledgement, audited expiring snooze, per-incident notification streams, higher-severity snooze override, backlog/notification/review metrics, and globally ordered implemented authority mutations.
- Added durable source-health transition history covering initial health, timeout, failure, and recovery.
- Made analysis, incident, notification, opportunity, and source-health identities deterministic for fixture replay.
- Added deterministic, structured After-Event Review generation with coverage gaps, delays, service misses, unresolved actions, explicit unassessed ground-truth dimensions, content hashing, and tamper verification.
- Added release-candidate inventory identity, truthful H0 admission status, atomic candidate writing, and repository-tamper verification.
- Expanded the REST API and CLI for configuration, review, notifications, authority/source journals, After-Event Review, and release-candidate verification.
- Expanded the development suite from 25 to 36 passing tests.

## 0.2.0 — 2026-08-02

- Added durable source boot/clock-epoch/sequence cursors and event-time watermarks.
- Added incident-journal restart reconstruction and duplicate-analysis suppression.
- Replaced wall-clock deadline decisions with an injectable monotonic clock and deterministic virtual clock.
- Added approved-profile admission, maximum-deferral handling, overload declaration, and explicit scheduler projections.
- Added pre-scheduler opportunity records with complete terminal reconciliation and deterministic schedule digests.
- Added an open-loop deterministic B0/B1/O1 replay laboratory with per-opportunity timing and truthful simulated-claim labels.
- Added atomic content-addressed artifacts, capacity reserve enforcement, interrupted-write quarantine, and claim evidence closure.
- Added separate operational capability states and runtime/opportunity/journal API projections.
- Expanded the development suite from 16 to 25 passing tests.

## 0.1.0 — 2026-08-02

- Established a legacy delivery framework full-scope delivery graph for all 743 functional requirements and 193 ADRs.
- Added the six-component Python implementation boundary.
- Added normalized observation contracts, bounded source buffers, four hazard adapters, criticality/EDF scheduling, Tier-A reservation, sole-authority incident journaling, deterministic scenario replay, REST API, CLI, release manifest, architecture policy, and tests.
- Preserved unimplemented target-device, learned-model, physical-signal, live-source, field, security-hardening, and release-evidence work as confirmed legacy delivery framework backlog rather than paper compliance.
