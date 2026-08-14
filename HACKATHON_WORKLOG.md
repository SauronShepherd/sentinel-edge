# Sentinel Edge Hackathon Worklog

## Globally ordered authority journal — REQ-AJL-001

Added authority-journal positions with unique epoch/ordinal/sequence tuples and a predecessor chain for accepted mutations.

Changed paths: `src/sentinel_edge/audit/authority_journal.py`, `tests/test_authority_journal.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_authority_journal.py`

Receipt: `provenance/evidence/705610908a7da0dd8035381d5863dfc51c791003d64109a5812c3258d66b1be6.json` (1 passed; H0 emulated aarch64 qualification).

## 2026 JRC European flood-depth research asset — REQ-SRC-002

Added an offline research/evaluation card preserving 2015–2024 coverage, 20 m resolution, GFM/Sentinel-1 derivation, centimetre encoding, permanent-water sentinel semantics, CC BY 4.0 licensing, and no-current-local-truth role.

Changed paths: `src/sentinel_edge/qualification/jrc_flood_maps.py`, `tests/test_jrc_flood_maps.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_jrc_flood_maps.py`

Receipt: `provenance/evidence/3d42e5085a948ec10411c4cedc3dcea878d69563a20090849fe9b2f2c0652b20.json` (1 passed; H0 emulated aarch64 qualification).

## Drift campaign scenarios — REQ-DRF-008

Added deterministic brightness/scene, sensor bias/noise, missingness, source-version, and prevalence-shift scenarios. Each produces an explicit limitation that synthetic shift does not prove real-world concept drift and a review/abstain action.

Changed paths: `src/sentinel_edge/qualification/drift_campaign.py`, `tests/test_drift_campaign.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_drift_campaign.py`

Receipt: `provenance/evidence/b1e40850c89f211ea3a92fccbb1bc6943206b5a3008c65a63c6618844a43ddb7.json` (1 passed; H0 emulated aarch64 qualification).

## Profile drift governance — REQ-DRF-007

Added owner, timezone-aware review deadline, interim permitted effect, and rollback profile for suspect/expired profiles. Expired findings deterministically select rollback instead of remaining indefinitely under review.

Changed paths: `src/sentinel_edge/qualification/profile_governance.py`, `tests/test_profile_governance.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_profile_governance.py`

Receipt: `provenance/evidence/a59b2d1b545b44f4f852ad83398cf5583ce496e0eebefb6ffae705af44c09c47.json` (1 passed; H0 emulated aarch64 qualification).

## Selective-risk calibration — REQ-DRF-006

Added calibration reporting that preserves abstention, recall, false-alert, entropy-shift, and critical-subgroup metrics. Subgroup failures remain explicit and cannot be hidden by aggregate entropy/input-shift values.

Changed paths: `src/sentinel_edge/qualification/risk_calibration.py`, `tests/test_risk_calibration.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_risk_calibration.py`

Receipt: `provenance/evidence/10f02b6e7cfa776b474ba3852dca296eb5cd4d72eacd47193190a2cd32adc0c3.json` (1 passed; H0 emulated aarch64 qualification).

## Time-source fault matrix — REQ-CTS-007

Added deterministic safe outcomes and reason codes for spoof, replay, delay, rollback, forward-step, source-switch, certificate-expiry, and offline-reboot faults.

Changed paths: `src/sentinel_edge/qualification/time_faults.py`, `tests/test_time_faults.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_time_faults.py`

Receipt: `provenance/evidence/2572ce87c7f2bb5892f19ed4a17d8b3fbeb4d374f9e4967b8662858969aafb8a.json` (1 passed; H0 emulated aarch64 qualification).

## NTS authentication and fallback state — REQ-CTS-003

Added explicit NTS authentication, failure reason, fallback mode, and trusted-status fields. Fallback cannot silently retain trusted time status.

Changed paths: `src/sentinel_edge/qualification/nts_state.py`, `tests/test_nts_state.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_nts_state.py`

Receipt: `provenance/evidence/b489035dd698a0b27cd4a27b5982609d85ce25ac1f9f9bdb9ab56c2586afefe5.json` (2 passed; H0 emulated aarch64 qualification).

## Root-integrity deployment boundary — REQ-HBT-005

Added deployment-readiness policy requiring either a qualified boot profile or an explicit powered-off/privileged-host limitation. Unverified hosts cannot claim end-to-end protection.

Changed paths: `src/sentinel_edge/qualification/root_integrity.py`, `tests/test_root_integrity.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_root_integrity.py`

Receipt: `provenance/evidence/a5557aa2bfc498669c559907075f451c4498e52deb5e60799ddc947a6a16d554.json` (2 passed; H0 emulated aarch64 qualification).

## Exact secure-boot fixture boundary — REQ-HBT-004

Added secure-boot fixture verification requiring exact board/EEPROM/image/key-lifecycle/recovery metadata. Unsigned, wrong-key, and rollback fixtures fail; recovery cannot expose the signing private key.

Changed paths: `src/sentinel_edge/qualification/secure_boot_fixture.py`, `tests/test_secure_boot_fixture.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_secure_boot_fixture.py`

Receipt: `provenance/evidence/40a31c6bdafef5f215765deb3229f9e02693683356c4273beeecfde37fa621c1.json` (1 passed; H0 emulated aarch64 qualification).

## Simultaneous-event I/O pressure transcript — REQ-IOP-008

Added a reconciled transcript for queue age, pressure, shedding, missed evidence, and deadline outcomes during controlled I/O pressure scenarios.

Changed paths: `src/sentinel_edge/qualification/io_pressure_transcript.py`, `tests/test_io_pressure_transcript.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_io_pressure_transcript.py`

Receipt: `provenance/evidence/f76393ec82123314fb4ecf0019a561c40bc127e89b99c058ef2207f2f52912bb.json` (1 passed; H0 emulated aarch64 qualification).

## Explicit truth on media persistence failure — REQ-IOP-007

Added an outcome contract requiring incident transitions to remain recorded when rich media cannot be persisted, with explicit degraded/evidence-unavailable state and no fabricated complete bundle.

Changed paths: `src/sentinel_edge/runtime/media_persistence.py`, `tests/test_media_persistence.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_media_persistence.py`

Receipt: `provenance/evidence/264956092e3b46162bc6365adf4ba9e499da856ee35af47f8dce1b94aabb9148.json` (2 passed; H0 emulated aarch64 qualification).

## I/O and persistence-tail qualification envelope — REQ-IOP-005

Added benchmark-host envelope checks for I/O PSI, fsync, WAL checkpoint, and evidence-encoding tails. Out-of-envelope stalls disallow headline latency/energy claims and receive an explicit label.

Changed paths: `src/sentinel_edge/qualification/io_envelope.py`, `tests/test_io_envelope.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_io_envelope.py`

Receipt: `provenance/evidence/877210508525dead28f0011752656e7100c9fbba9406606b813857d312c135fd.json` (2 passed; H0 emulated aarch64 qualification).

## Critical I/O reserve — REQ-IOP-004

Added reserved free-space and bounded append/fsync limits for critical incident truth, review, and disposition records. Optional media writes are rejected when they would consume the reserve.

Changed paths: `src/sentinel_edge/storage/critical_reserve.py`, `tests/test_critical_reserve.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_critical_reserve.py`

Receipt: `provenance/evidence/8286d0a34d533d64d5785a1283e9a38adea338ac0098c7017aaac6510331a476.json` (1 passed; H0 emulated aarch64 qualification).

## Critical-truth I/O shedding — REQ-IOP-003

Added deterministic pressure handling that sheds previews, optional transcoding, telemetry, research exports, backup, and garbage collection before critical truth/evidence metadata, while marking degraded state.

Changed paths: `src/sentinel_edge/runtime/io_shedding.py`, `tests/test_io_shedding.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_io_shedding.py`

Receipt: `provenance/evidence/773d1a7266bbe05f556c4f2f7f4b373275dad767c741022edb5a5216dacbf254.json` (2 passed; H0 emulated aarch64 qualification).

## Bounded I/O workload expectations — REQ-IOP-002

Added a workload registry record declaring read/write limits, fsync requirement, temporary-space limit, I/O class, criticality, and durability expectation.

Changed paths: `src/sentinel_edge/qualification/io_expectations.py`, `tests/test_io_expectations.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_io_expectations.py`

Receipt: `provenance/evidence/b2c159aed0f1d6649a867c690934e82327e64d289674110e0fbf8fbea022a7a8.json` (1 passed; H0 emulated aarch64 qualification).

## I/O pressure and durability-tail snapshot — REQ-IOP-001

Added a diagnostic snapshot for I/O PSI, dirty/writeback, fsync, WAL checkpoint, evidence-encoding tails, CPU pressure, and memory pressure. Missing metrics are explicit and classification distinguishes I/O stalls from CPU/memory pressure.

Changed paths: `src/sentinel_edge/qualification/io_pressure.py`, `tests/test_io_pressure.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_io_pressure.py`

Receipt: `provenance/evidence/d41b99af84edbedb27d52c84ccb22660c9cd948c44b6adda29feef8e4172b060.json` (2 passed; H0 emulated aarch64 qualification).

## Purpose-bound benchmark claim access — REQ-BGV-006

Added auditable claim-set access receipts requiring claim-set identity, purpose, actor, and audit event identity.

Changed paths: `src/sentinel_edge/benchmark/claim_access.py`, `tests/test_claim_access.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_claim_access.py`

Receipt: `provenance/evidence/692ac60f49c86fd9dc5bc125cfe36841feb4c65d86a26ce58447c8fda7c64699.json` (2 passed; H0 emulated aarch64 qualification).

## Arrival jitter and instrumentation overhead — REQ-ARR-006

Added a benchmark-quality report that compares load-generator arrival jitter and instrumentation overhead against a qualified envelope, labeling or invalidating out-of-envelope blocks.

Changed paths: `src/sentinel_edge/benchmark/arrival_quality.py`, `tests/test_arrival_quality.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_arrival_quality.py`

Receipt: `provenance/evidence/c6ca0c4fbfbda2220f13ac5bf54fc2faab68a9a57fb1048546bc4bba288e1b5e.json` (2 passed; H0 emulated aarch64 qualification).

## Synthetic judge backup/restore fixture — REQ-BPR-006

Added a judge restore fixture contract requiring synthetic content and offline public verification material, while rejecting hidden private decryption requirements.

Changed paths: `src/sentinel_edge/qualification/judge_restore.py`, `tests/test_judge_restore.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_judge_restore.py`

Receipt: `provenance/evidence/5f9129f7063b31c9ea0b80bc3b69bda72a649cd6d78f3e127959e0fb861e95da.json` (2 passed; H0 emulated aarch64 qualification).

## Signed native artifact qualification — REQ-MGT-006

Added fail-closed admission evidence for custom native artifacts, requiring a separate signature plus ABI, compiler, hardening, sandbox, and attack evidence before activation.

Changed paths: `src/sentinel_edge/runtime/native_artifact_qualification.py`, `tests/test_native_artifact_qualification.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_native_artifact_qualification.py`

Receipt: `provenance/evidence/90a0ebcf9e81c79e8f1f5800a0aa067b0c040db98e62de4f82cbb060886f8036.json` (2 passed; H0 emulated aarch64 qualification).

## NASA LHASA/IMERG context assets — REQ-SMD-003

Added offline dataset-card policy for NASA LHASA L4 v2.0.0 and IMERG/LHASA Exposure Maps 1.0, requiring role and latency/coverage caveats, preserving archive/catalog mismatch, and rejecting local-truth authority.

Changed paths: `src/sentinel_edge/qualification/lhasa_assets.py`, `tests/test_lhasa_assets.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_lhasa_assets.py`

Receipt: `provenance/evidence/5244936f842e12e77485928f33cf87a90c38e128bddc79ba575377492fb779ec.json` (2 passed; H0 emulated aarch64 qualification).

## Restricted local evidence at-rest protection — REQ-LDE-001/002/003

Added an explicit deployment threat profile, qualified full-disk/application-authenticated encryption modes, and logically separate key authority. Copied evidence-volume access fails without the designated authority.

Changed paths: `src/sentinel_edge/privacy/local_evidence_protection.py`, `tests/test_local_evidence_protection.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_local_evidence_protection.py`

Receipt: `provenance/evidence/d1f7817f5ddd8417b89cab39de81a13edb95b618c46d36abde3dea77f5a46352.json` (2 passed; H0 emulated aarch64 qualification).

## Complete-pipeline CV ablation — REQ-CV-002

Added paired CV ablation evidence covering preprocessing, inference, postprocessing, fallback use, and explicit rejection of inherited external benchmark values.

Changed paths: `src/sentinel_edge/qualification/cv_ablation.py`, `tests/test_cv_ablation.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_cv_ablation.py`

Receipt: `provenance/evidence/28f674048b4edcf46c417104a84e51819138ee2c13082f74f5ed1eb85dcbd2b0.json` (2 passed; H0 emulated aarch64 qualification).

## EGMS historical context — REQ-EGM-001

Added bounded EGMS 2020-2024 machine-to-machine context preserving release period, product, API/fixture reference, T3 tier, and historical-only status.

Changed paths: `src/sentinel_edge/integrations/egms.py`, `tests/test_egms.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_egms.py`

Receipt: `provenance/evidence/07265f76d08ce23c9a340880e8488ad0ed2ce277aba6b673aae995c59d7c2856.json` (2 passed; H0 emulated aarch64 qualification).

## FIRMS lineage and availability — REQ-FIR-001/002

Added FIRMS observation lineage for sensor, product, processing class, and correlation family. Added availability states whose missing dates reduce completeness without fabricating a negative fire observation.

Changed paths: `src/sentinel_edge/integrations/firms.py`, `tests/test_firms.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_firms.py`

Receipt: `provenance/evidence/91bd1e90814d884cb3d1718731d5dc06ec34ed2f765a6aa5d3f28680778b868a.json` (2 passed; H0 emulated aarch64 qualification).

## Time-boxed real-time scheduling experiment — REQ-OSS-002

Added a watchdog-bounded privileged scheduling experiment result that records timeout and explicitly cannot replace default proof.

Changed paths: `src/sentinel_edge/qualification/realtime_experiment.py`, `tests/test_realtime_experiment.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_realtime_experiment.py`

Receipt: `provenance/evidence/a9e6d6fdfd9eaa14b288dff0d1b30d26e07281abb0252e9528d76a02c7b00208.json` (2 passed; H0 emulated aarch64 qualification).

## Complete-node energy measurement window — REQ-ENG-003

Added an explicit scenario-bounded energy report that requires camera, storage, cooling, and idle components whenever instrumentation permits, and computes total watt-seconds over the declared window.

Changed paths: `src/sentinel_edge/qualification/energy_window.py`, `tests/test_energy_window.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_energy_window.py`

Receipt: `provenance/evidence/c3ba70441b6025614d04dc5353993a46491e2702dcc427be4c12b42434e4e060.json` (2 passed; H0 emulated aarch64 qualification).

## Automatic OTA retrieval boundary — REQ-UPD-007

Added explicit OTA policy metadata showing automatic retrieval is optional and cannot be an acceptance or release-gate dependency, matching the registry’s hackathon boundary.

Changed paths: `src/sentinel_edge/update/ota_policy.py`, `tests/test_ota_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_ota_policy.py`

Receipt: `provenance/evidence/5e8716d7a93417c988a3c482a2d47a574c59b8551f317b5b9367f5698f364766.json` (2 passed; H0 emulated aarch64 qualification).

## Update activation preconditions — REQ-UPD-004

Added explicit power, storage, and compatibility activation preconditions. Any unsafe precondition fails closed before the active release can be changed.

Changed paths: `src/sentinel_edge/update/preconditions.py`, `tests/test_update_preconditions.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_update_preconditions.py`

Receipt: `provenance/evidence/8bf279cc238e0c5fe611b6c1e40c40c8371bffcf6c35b7c2fdef7f1b20ac2e96.json` (4 passed; H0 emulated aarch64 qualification).

## C2PA export transformation credential — REQ-EXP-004

Added export metadata for C2PA-style credentials that records asset digest, issuer, and transformations while rejecting any sensor-truth claim.

Changed paths: `src/sentinel_edge/exports/c2pa.py`, `tests/test_c2pa_export.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_c2pa_export.py`

Receipt: `provenance/evidence/28e71820d35d799ae1e99ba92a04f7729e29b46061e441078b7156bd1e23fd0c.json` (2 passed; H0 emulated aarch64 qualification).

## Time-boxed ACL diagnostic — REQ-RUN-005

Added an optional ACL diagnostic with bounded execution, timeout reporting, cancellation, and an explicit invariant that diagnostic outcomes never block release gates.

Changed paths: `src/sentinel_edge/runtime/acl_diagnostic.py`, `tests/test_acl_diagnostic.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_acl_diagnostic.py`

Receipt: `provenance/evidence/bae1a5e65556100a38cc4228bf72c88a138f01b527edd337299d78cb5a70b229.json` (2 passed; H0 emulated aarch64 qualification).

## Workflow correctness paths — REQ-AWF-003

Extended both Arazzo workflows with an explicit proof-path contract covering retry, idempotency, optimistic conflict, and REST resynchronization; validation fails if any path is missing.

Changed paths: `src/sentinel_edge/workflows/arazzo.py`, `fixtures/workflows/upload-review.arazzo.yaml`, `fixtures/workflows/cursor-resync.arazzo.yaml`, `tests/test_arazzo_workflows.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_arazzo_workflows.py`

Receipt: `provenance/evidence/6af6d08457eb0871e685728b8bdd0b1174ce52f5964c12d0df8ac58f92960f58.json` (3 passed; H0 emulated aarch64 qualification).

## Pinned offline Arazzo workflows — REQ-AWF-001/002

Added Arazzo 1.1 upload-review and cursor-resync workflow artifacts plus deterministic validation that rejects uncontrolled external OpenAPI references.

Changed paths: `src/sentinel_edge/workflows/arazzo.py`, `fixtures/workflows/upload-review.arazzo.yaml`, `fixtures/workflows/cursor-resync.arazzo.yaml`, `tests/test_arazzo_workflows.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_arazzo_workflows.py`

Receipt: `provenance/evidence/a2fb65cc58c40864c375d6b3a4868301e710dc285f65e393cbe2a48d79af72b7.json` (3 passed; H0 emulated aarch64 qualification).

## Bounded idempotency receipts — REQ-IDM-006

Added privacy-safe idempotency receipts that retain only payload digests and results, replay delayed retries once, reject digest conflicts, expire by replay window, and enforce a maximum entry count.

Changed paths: `src/sentinel_edge/security/idempotency_receipts.py`, `tests/test_idempotency_receipts.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_idempotency_receipts.py`

Receipt: `provenance/evidence/70d141d22db4b2ddbf981c186f5434340adaad2ab0be606f60df782fa7ecb1f2.json` (3 passed; H0 emulated aarch64 qualification).

## Non-authoritative identifier semantics — REQ-IDM-005

Added explicit classification for correlation, sortable/public, database and content identifiers. Identifier possession is rejected as an authorization mechanism for every kind.

Changed paths: `src/sentinel_edge/security/identifier_authority.py`, `tests/test_identifier_authority.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_identifier_authority.py`

Receipt: `provenance/evidence/9d82a2d130dede81051c77431f2e8421211698eef760a9f54ee8e8754c30861c.json` (1 passed; H0 emulated aarch64 qualification).

## Vulnerability contact and support period — REQ-VUL-001/002

Added product support metadata for security contact, supported versions, intended support start/end dates, and explicit non-CRA-conformity posture. Invalid periods or missing versions fail closed.

Changed paths: `src/sentinel_edge/release/support_policy.py`, `tests/test_support_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_support_policy.py`

Receipt: `provenance/evidence/8d64cb98fb9a867113b659c0bd688f78c6574e96ff05c73d313f38efa9b0cc26.json` (2 passed; H0 emulated aarch64 qualification).

## Preclipped exposure context — REQ-IMP-001

Added exposure-context asset policy for GHSL, WorldPop, and attributed OSM inputs. Assets must be preclipped and offline, with attribution, and are explicitly limited to potential-exposure context rather than hazard truth.

Changed paths: `src/sentinel_edge/qualification/exposure_context.py`, `tests/test_exposure_context.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_exposure_context.py`

Receipt: `provenance/evidence/3a5c3f320ce0cf635494b0371ce4b30a0433b795a49db3fd5836e421cdd2db18.json` (2 passed; H0 emulated aarch64 qualification).

## Pinned transform environment — REQ-GRP-001

Added a transform-environment pin manifest requiring exact pyproj/PROJ versions, `proj.db` digest, grid digests, transform policy, and environment digest. Incomplete runtime identity cannot qualify.

Changed paths: `src/sentinel_edge/geospatial/pin_manifest.py`, `tests/test_transform_pin_manifest.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_transform_pin_manifest.py`

Receipt: `provenance/evidence/17a2d6e6cdfacdd9e1ba1392a14e092ecaeecf9b2082e75c45887647ad5d42d5.json` (2 passed; H0 emulated aarch64 qualification).

## Versioned schema evolution boundaries — REQ-EVO-001

Verified explicit schema versions on observation contracts, peer handshakes, migration records, and database migration rehearsals, with raw/normalized payload lineage preserved.

Changed paths: `src/sentinel_edge/evolution/contracts.py`, `tests/test_schema_evolution.py`, `tests/test_observation_contract_adapters.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_schema_evolution.py tests/test_observation_contract_adapters.py`

Receipt: `provenance/evidence/60d23de955030cd186757a4db929d6198a736bbfdd6a4b6e3048752bf4b3e3d3.json` (6 passed; H0 emulated aarch64 qualification).

## EGMS historical-only boundary — REQ-EGM-002

Verified EGMS deformation records require an explicit historical-only declaration; unqualified records are rejected and historical context cannot influence live movement decisions.

Changed paths: `src/sentinel_edge/qualification/landslide_context.py`, `tests/test_landslide_context.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_landslide_context.py`

Receipt: `provenance/evidence/1a51c8e79b2d7df146e6f2ea92c836280a778db62bcb91b70721d09beb7ffd4f.json` (3 passed; H0 emulated aarch64 qualification).

## OpenHydroNet offline research boundary — REQ-SV-005

Verified OpenHydroNet is classified as offline research/evaluation input and cannot influence incident state or H0 quality claims until an independent promotion gate passes.

Changed paths: `src/sentinel_edge/qualification/research_assets.py`, `tests/test_openhydronet_research.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_openhydronet_research.py`

Receipt: `provenance/evidence/7901414e3ee17e3964a27f9b4fd40edaced7b5651c28d16b93a121a6c335683e.json` (1 passed; H0 emulated aarch64 qualification).

## Signed release attestations and vetted predicates — REQ-ATT-001/002

Verified signed attestation subject binding, signer/builder policy enforcement, pinned attestation schema, and use of the SLSA provenance predicate rather than duplicative custom predicates.

Changed paths: `src/sentinel_edge/release/independent_build.py`, `src/sentinel_edge/release/provenance.py`, `tests/test_attestation_policy.py`, `tests/test_provenance_and_advisories.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_attestation_policy.py tests/test_provenance_and_advisories.py`

Receipt: `provenance/evidence/f4be8a5eb8c7fa751b5030abb155cfcc58c448a6134a1252189bd97bd21dc9a3.json` (8 passed; H0 emulated aarch64 qualification).

## Release status snapshot — REQ-RSB-006

Added compact release-status reporting for H0 total/closed/delta, declared critical path, exceptions, and optional-work budget. Inconsistent deltas or absent critical paths fail closed.

Changed paths: `src/sentinel_edge/release/status_snapshot.py`, `tests/test_release_status_snapshot.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_status_snapshot.py`

Receipt: `provenance/evidence/82cd07fdb7822b2a118388aa4b699281078f33d5c25d396050cddd60273e2b30.json` (2 passed; H0 emulated aarch64 qualification).

## Privacy-aware location evidence — REQ-LOC-001

Added time-varying location evidence with timezone-aware observation time, precision, derivation, privacy class, and consent basis. Restricted/private location records fail closed without consent or precision.

Changed paths: `src/sentinel_edge/privacy/location_evidence.py`, `tests/test_location_evidence.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_location_evidence.py`

Receipt: `provenance/evidence/e9326aacbe8f6f22cab8d1004bb1e3c3d2bcc3577e38a19382276344aaf39a54.json` (2 passed; H0 emulated aarch64 qualification).

## Geospatial change-impact mapping — REQ-GRP-013

Added immutable impact records mapping PROJ/EPSG/grid changes to affected operations, rerun tests, and claims. Material changes fail record construction unless operation/test impact is explicitly declared.

Changed paths: `src/sentinel_edge/geospatial/change_impact.py`, `tests/test_geospatial_change_impact.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_geospatial_change_impact.py`

Receipt: `provenance/evidence/2403f2c1141c55ca441e7f62e3ab32d840d886f0a055ee0df27fd07a98ad08da.json` (2 passed; H0 emulated aarch64 qualification).

## Derived spatial provenance — REQ-GRP-012

Added immutable derived spatial results that require and preserve selected operation, grid identities, and accuracy metadata alongside derived values.

Changed paths: `src/sentinel_edge/geospatial/derived_result.py`, `tests/test_derived_spatial_result.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_derived_spatial_result.py`

Receipt: `provenance/evidence/6298978160431c7052aab87c45e65f97fc83c933e5083761f8b3b36659ba8922.json` (2 passed; H0 emulated aarch64 qualification).

## Geospatial known-answer harness — REQ-GRP-011

Added deterministic transform known-answer checks with declared tolerances and expected non-identity enforcement, covering horizontal/vertical/epoch-style result classes and fail-closed mismatch reasons.

Changed paths: `src/sentinel_edge/geospatial/known_answers.py`, `tests/test_geospatial_known_answers.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_geospatial_known_answers.py`

Receipt: `provenance/evidence/05b6ba42efc01269f7465a244d48cb08142cec4aa6df7173aae8a42643d90c38.json` (2 passed; H0 emulated aarch64 qualification).

## Pinned geospatial grids and fallback rejection — REQ-GRP-010

Added required-grid identity validation and rejection of ballpark, identity, and no-grid fallback operations. Missing required grids produce explicit review/failure reason codes.

Changed paths: `src/sentinel_edge/geospatial/transform_declarations.py`, `tests/test_required_grids.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_required_grids.py`

Receipt: `provenance/evidence/5913990ab1afee202b8141a6953b8eaf47e05769e5ff0bf92aec1019f3fae53b.json` (2 passed; H0 emulated aarch64 qualification).

## Explicit CRS transform declarations — REQ-GRP-009

Added transform declarations requiring source/target CRS, selected operation, area of use, coordinate epoch, and accuracy. Ballpark operations and unresolved epochs fail qualification.

Changed paths: `src/sentinel_edge/geospatial/transform_declarations.py`, `tests/test_transform_declarations.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_transform_declarations.py`

Receipt: `provenance/evidence/6f2bb95596da23f970ddd1a8aec763bd92f2dfaa0e9f12553521b012b648bd4f.json` (3 passed; H0 emulated aarch64 qualification).

## Bounded reevaluation queue — REQ-REV-006

Added bounded reevaluation queue/resource controls with explicit terminal `incomplete` and `failed` states; capacity overflow fails closed rather than silently dropping work.

Changed paths: `src/sentinel_edge/review/reevaluation_queue.py`, `tests/test_reevaluation_queue.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_reevaluation_queue.py`

Receipt: `provenance/evidence/91b07fc534db4d017a53faa92cebc6613f59dfccc1213caba760edb34e9476d1.json` (2 passed; H0 emulated aarch64 qualification).

## Separate decision reconstruction and reevaluation — REQ-REV-002

Added an immutable audit view preserving what was known at original decision time separately from current-policy/current-evidence reevaluation, with explicit non-rewrite marking.

Changed paths: `src/sentinel_edge/review/decision_reconstruction.py`, `tests/test_decision_reconstruction.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_decision_reconstruction.py`

Receipt: `provenance/evidence/950934acb844b965c3820497916d7eaf7e7b8d386dab140fcbc4058d4108c874.json` (1 passed; H0 emulated aarch64 qualification).

## Actual PROJ runtime identity — REQ-GRP-008

Added an explicit observed PROJ runtime identity requiring loaded library, data directory, `proj.db` digest, and grid digests. Required-grid absence is reported as unqualified; package-name inference is rejected.

Changed paths: `src/sentinel_edge/geospatial/runtime_identity.py`, `tests/test_geospatial_runtime_identity.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_geospatial_runtime_identity.py`

Receipt: `provenance/evidence/9209eab6a24bf609aa57c896741041c1720ed65df9955752a713f98cef13bf1f.json` (3 passed; H0 emulated aarch64 qualification).

## Missing geospatial operation fail-safe — REQ-GRP-006

Verified a required transform without a qualified operation enters `review_required`, preserves limitation reason codes, and emits no normalized geometry for downstream decision use.

Changed paths: `src/sentinel_edge/geospatial/contracts.py`, `tests/test_geospatial_missing_operation.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_geospatial_missing_operation.py`

Receipt: `provenance/evidence/6440c38f1a13913ca41f9d901af97b54cf893a388893b415cee55bbfb6855f95.json` (1 passed; H0 emulated aarch64 qualification).

## Geospatial transform safety — REQ-GRP-003/004

Verified non-qualified or ballpark-like transforms fail to `review_required` without normalized geometry, while the spatial report preserves the declared transform pipeline and limitation reason codes.

Changed paths: `src/sentinel_edge/geospatial/contracts.py`, `tests/test_geospatial_transform_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_geospatial_transform_policy.py`

Receipt: `provenance/evidence/3cac4f1926c762b642a321253161acfa0498e913a0c76afd11876dd065f8d33c.json` (2 passed; H0 emulated aarch64 qualification).

## Bounded authorization outcome history — REQ-AZF-004/005

Added bounded same-boot point-in-time authorization records with expiry and commit-time reauthorization. Original acceptance remains immutable while commit denial/reconfirmation and its reason are recorded.

Changed paths: `src/sentinel_edge/security/authorization_history.py`, `tests/test_authorization_history.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_authorization_history.py`

Receipt: `provenance/evidence/86a0028d470a7d704cbacc6adfca72bcd525643f9deb23e979351b3fca3cb273.json` (2 passed; H0 emulated aarch64 qualification).

## Critical storage reserve — REQ-ABX-003

Verified content-addressed artifact admission reserves bounded capacity for critical incident truth and candidate proof, while noncritical previews/telemetry are rejected before the reserve is consumed. Critical artifacts retain access to the protected capacity.

Changed paths: `src/sentinel_edge/storage/artifacts.py`, `src/sentinel_edge/storage/artifact_governance.py`, `tests/test_artifacts_and_claims.py`, `tests/test_artifact_governance.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_artifacts_and_claims.py tests/test_artifact_governance.py`

Receipt: `provenance/evidence/e54392319489ceee012dc52cf9a8c75dd955ee5a8858ecbf53c6f9a1f6d2db00.json` (10 passed; H0 emulated aarch64 qualification).

## Bounded opaque projection cursors — REQ-CUR-004/006

Added cursor-policy validation enforcing a bounded lifetime and finite buffer policy, while accepting only opaque UUID/position/version/digest-scope encoding and rejecting plaintext private details.

Changed paths: `src/sentinel_edge/projections/cursor_policy.py`, `tests/test_cursor_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_cursor_policy.py`

Receipt: `provenance/evidence/29d8e47450c960d7cbf8b3fc4d03e98cb877067e382c8a0c3793cb934b2717e8.json` (1 passed; H0 emulated aarch64 qualification).

## Immutable benchmark eligibility aggregation — REQ-BGV-008

Verified digest-bound benchmark aggregation over signed plans, attempted candidates, run restrictions, and result eligibility. Independent report verification reproduces headline eligibility and detects tampering.

Changed paths: `src/sentinel_edge/benchmark/governance.py`, `tests/test_benchmark_governance_v018.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_governance_v018.py`

Receipt: `provenance/evidence/71a5ea571ea47fb55539010abe8c0de8a0605c47bfd367d37799f8bdfdad20c9.json` (9 passed; H0 emulated aarch64 qualification).

## Predeclared benchmark endpoints — REQ-BGV-005

Verified the signed benchmark-plan lane predeclares primary metrics and selection treatment; exploratory reports remain ineligible for frozen headline claims, preventing favorable post-hoc metric selection.

Changed paths: `src/sentinel_edge/benchmark/governance.py`, `tests/test_benchmark_governance_v018.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_benchmark_governance_v018.py`

Receipt: `provenance/evidence/c0f917b70f907aeb209964ad3c46e5f65270d4fc9cbdb7db63445f1191bf2b6c.json` (9 passed; H0 emulated aarch64 qualification).

## Exact release capability profile — REQ-CQL-003

Added a machine-readable release profile contract requiring explicit enumeration of enabled, disabled, emulated, fixture-only, degraded, and unsupported capability paths, with a reason for every entry.

Changed paths: `src/sentinel_edge/release/profile.py`, `tests/test_release_profile.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_profile.py`

Receipt: `provenance/evidence/74e2c2bd775f59c27e78f2c27cd8e73c14f1e19be109d63ecf49ee4d7ef2d9de.json` (2 passed; H0 emulated aarch64 qualification).

## Attributable metadata conflicts — REQ-SMD-001/002

Added metadata assertions preserving source/value provenance. Conflicting decision-relevant values cannot be silently precedence-resolved and instead produce `review_required`; matching values may use an explicitly declared precedence.

Changed paths: `src/sentinel_edge/qualification/metadata_conflicts.py`, `tests/test_metadata_conflicts.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_metadata_conflicts.py`

Receipt: `provenance/evidence/78bfdf866809db54e4cb7d70f9707d2ad41b702037ed086330d03111656cee93.json` (2 passed; H0 emulated aarch64 qualification).

## Non-authoritative presentation metadata — REQ-EXT-005

Added a presentation metadata boundary that returns labels, profiles, and caveats separately from authoritative state and explicitly marks them non-authoritative. Client display values cannot alter the server state machine.

Changed paths: `src/sentinel_edge/gateway/presentation_metadata.py`, `tests/test_presentation_metadata.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_presentation_metadata.py`

Receipt: `provenance/evidence/6b57c869df51404fc270b9d204abe72734867f523bb8f6a2b102489367fa2805.json` (1 passed; H0 emulated aarch64 qualification).

## Encrypted restricted backups and separate recovery authority — REQ-BDR-001/005

Verified the authenticated-encryption backup envelope and separate recovery-key reference. Backup bytes do not contain plaintext or key material; copied backup data cannot decrypt without the designated recovery key.

Changed paths: `src/sentinel_edge/storage/encrypted_backup.py`, `tests/test_encrypted_backup.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_encrypted_backup.py`

Receipt: `provenance/evidence/16ec37bb27e6e6380fb85d439e422babaee6bd7b9cdb96d4e54886310650d8c3.json` (2 passed; H0 emulated aarch64 qualification).

## Auditable corrective-action lifecycle — REQ-ACT-001

Added corrective-action records with owner, priority, due state, requirement/test linkage, closure evidence, and append-only lifecycle audit. Closed and accepted-debt transitions require explicit evidence.

Changed paths: `src/sentinel_edge/review/corrective_actions.py`, `tests/test_corrective_actions.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_corrective_actions.py`

Receipt: `provenance/evidence/8b97a4976428cbec5d3af869ef7c764c579fb31379c1c8fae640dfb640007e4a.json` (2 passed; H0 emulated aarch64 qualification).

## Bounded offline schema references — REQ-API-001/002

Added local-only `$ref` resolution with explicit rejection of external references, bounded depth/node traversal, cycle protection, and sanitized bounded descriptions.

Changed paths: `src/sentinel_edge/gateway/schema_refs.py`, `tests/test_schema_refs.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_schema_refs.py`

Receipt: `provenance/evidence/baeff31f38712335cb937c2936efa639e6ac519b27491a619ef3d87ea8573f6a.json` (2 passed; H0 emulated aarch64 qualification).

## Bounded post-fire context — REQ-PFC-001/002

Added post-fire context evaluation requiring spatial overlap and a bounded freshness/decay window. Valid context can only recommend cadence/review effects; it cannot influence hazard state.

Changed paths: `src/sentinel_edge/qualification/post_fire_context.py`, `tests/test_post_fire_context.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_post_fire_context.py`

Receipt: `provenance/evidence/888b3f971e7b1a56b2aabccb94daaa52c10c7130c958bd0d44a0e07061e90b10.json` (2 passed; H0 emulated aarch64 qualification).

## Presentation artifact binding — REQ-RCI-006

Added a deterministic presentation-binding artifact for demo, screenshot, report-table and transcript files. It binds each file digest to the exact candidate ID and Claim Registry digest; candidate, registry, or file drift fails verification.

Changed paths: `src/sentinel_edge/release/presentation_binding.py`, `tests/test_presentation_binding.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_presentation_binding.py`

Receipt: `provenance/evidence/3968ebb1ba06efbb2be51c78f2399c18e3598a88684ecd181be9ba4a4a0ee8e0.json` (1 passed; H0 emulated aarch64 qualification).

## Append-only evidence state events — REQ-DGP-006/007

Added immutable evidence state events for redaction, erasure, external loss, restore and rebinding. Historical digest/profile fields remain attached to prior events; duplicate or out-of-order events fail closed.

Changed paths: `src/sentinel_edge/evidence/state_events.py`, `tests/test_evidence_state_events.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_evidence_state_events.py`

Receipt: `provenance/evidence/516e31f8556e8c6b14255680b2bd3cfd8a9a899f090e9f8863b9aab4472edebf.json` (2 passed; H0 emulated aarch64 qualification).

## Typed evidence targets and explicit availability states — REQ-DGP-004/005

Added evidence-registry binding that requires a typed target or explicitly records `unbound_target`; unknown digest profiles, unavailable content, and later redaction remain separate non-verified states.

Changed paths: `src/sentinel_edge/evidence/registry_binding.py`, `tests/test_evidence_registry_binding.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_evidence_registry_binding.py`

Receipt: `provenance/evidence/75e918e973bf440c6e3d6aea37192603d809130f471d9c34d02b970ef79bbe32.json` (3 passed; H0 emulated aarch64 qualification).

## Versioned digest profiles — REQ-DGP-001/002/003

Added versioned digest profiles declaring algorithm, canonicalization, purpose, privacy class and key version; profile-incompatible comparisons now resolve to incomplete evidence, and keyed digests are purpose-separated for protected identifiers.

Changed paths: `src/sentinel_edge/security/digest_profiles.py`, `tests/test_digest_profiles.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `HACKATHON_WORKLOG.md`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_digest_profiles.py`

Receipt: `provenance/evidence/cbc9ecfe7448c6d340092c43237310d77af2d68e41f4f151767e5272af3f6890.json` (3 passed; H0 emulated aarch64 qualification).

## Signed immutable release-candidate manifest — REQ-RCI-001

Added candidate-manifest construction binding the exact candidate digest, complete repository inventory digest, and signed manifest bytes. Verification fails closed on candidate-manifest tampering or signer mismatch.

Changed paths: `src/sentinel_edge/release/manifest.py`, `src/sentinel_edge/release/signing.py`, `src/sentinel_edge/release/__init__.py`, `tests/test_release_manifest_signing.py`, `registries/requirements.yaml`, `registries/tests.yaml`.

Exact command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_manifest_signing.py`

Receipt: `provenance/evidence/6adc0fc376795b4cf30761447949c64c6906c66fb3c7aa0737149682098972bc.json` (2 passed; H0 emulated aarch64 qualification).

## Platform/provider effective-interval observations — REQ-PRE-005

Implemented immutable, interval-bound platform/provider observations so historical incident or benchmark lookup remains tied to the external state effective at that time. Frozen artifact references are separate from mutable observation state, and overlapping intervals, invalid windows and naive timestamps fail closed.

Changed paths:

- `src/sentinel_edge/qualification/platform_observations.py`
- `tests/test_platform_observations.py`
- `registries/requirements.yaml`
- `registries/tests.yaml`
- `HACKATHON_WORKLOG.md`

Exact verification command:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_platform_observations.py
```

Receipt: `provenance/evidence/9ffbb44c5853e7c1f31592242b39416b414e234457d945859bf232bc09c8219e.json` (3 passed; H0 emulated aarch64 qualification).

This file records repository-local implementation work. It does not substitute for target, physical, field, or independent-review evidence.

## Emulated Arm64 hackathon release profile — H0-EMULATED-AARCH64-20260813

Adopted the explicit no-hardware hackathon profile. The canonical execution path is Docker/QEMU `linux/arm64` using `python:3.13-slim`; the guest reports `aarch64` while the host is reported separately. Physical sensors are not required for this profile. Hardware-specific performance, energy, thermal, and physical-sensor claims remain prohibited.

Changed paths:

- `config/arm64-emulation.yaml`
- `docker/Dockerfile.arm64`
- `scripts/dev.py`
- `architecture/command-catalog.yaml`
- `docs/release/EMULATED_ARM64_HACKATHON_PROFILE.md`
- `docs/release/CURRENT_SUBMISSION_READINESS.md`
- `docs/judge-guide.md`
- `docs/DEVELOPMENT_PLAN.md`
- `docs/OPEN_BLOCKERS.md`
- `README.md`

Exact verification commands:

```text
.venv\Scripts\python.exe scripts/dev.py arm64-setup
.venv\Scripts\python.exe scripts/dev.py arm64-doctor
.venv\Scripts\python.exe scripts/dev.py arm64-test
.venv\Scripts\python.exe scripts/validate_command_catalog.py
```

Receipts:

- `provenance/evidence/9b33b2932bcbd75fefc47dbeb1b58b3646cde2d22eb4eae8130a719782e966b6.json` (setup)
- `provenance/evidence/761dc7474d1899c2aa6d383f577bc144f5078aba7bd5e2afc0a6f15b58aaec1b.json` (doctor)
- `provenance/evidence/0b52244575908983a2a8818b25dcdfd867c04e345a6c1c99e050c2a9236ae827.json` (Arm64 bytecode lane)

Evidence scope: emulated AArch64 software execution and deterministic source checks only; no physical Raspberry Pi or sensor evidence.

The main doctor now also exposes the active hackathon profile, simulated input mode, and the fact that physical sensors are not required for this profile. Focused receipt: `provenance/evidence/bcd9fff38cc07d05ac2833a089d40d8cb885e7c595830c90db9aac79a4815ae3.json`.

The dependency-complete emulated image was then built with AArch64 wheels and used for the demo, simultaneous-event scenario, and benchmark replay.

Additional exact commands:

```text
.venv\Scripts\python.exe scripts/dev.py arm64-demo
.venv\Scripts\python.exe scripts/dev.py arm64-scenario
.venv\Scripts\python.exe scripts/dev.py arm64-benchmark
```

Receipts:

- `provenance/evidence/06591805fd36565080532f28637283a8006379b87e9038b45e5c96981eb08572.json`
- `provenance/evidence/4491c5cad3f9c148a57499b845a72053cd20dc09293208a3f09775e47faedbc5.json`
- `provenance/evidence/105bfe955be32125c8e73c7d0db3f00b97e09c4433971a0441692c4d22b3cadb.json`

Also removed duplicate test IDs from `registries/tests.yaml` through a mechanical normalization, updated `tests/test_audit_baseline.py` from 244 to the resulting authoritative 246 unique tests, and restored the legacy delivery framework validator to green. Exact checks:

```text
.venv\Scripts\python.exe scripts/validate_delivery_registry.py
.venv\Scripts\python.exe scripts/validate_conformance_ledger.py
.venv\Scripts\python.exe scripts/validate_evidence_registry.py
.venv\Scripts\python.exe scripts/validate_requirement_closure.py
.venv\Scripts\python.exe -m pytest -q tests/test_audit_baseline.py
```

The repository-wide `python scripts/dev.py test-all` lane was started with a five-minute bound but timed out without a completed result; it is not counted as passing evidence. Focused collaboration, doctor, registry, architecture, and emulated Arm64 lanes remain green.

Fail-fast repository audit then exposed and corrected stale expectations for the authoritative command count (39 → 49) and implementation-complete H0 count (237 → 238). Focused governance receipt: `provenance/evidence/96b9898991d49720ee0fd51b53dbef873c9e778968b6dbd988d52be948cad156.json`.

Partitioned suite audit found one additional stale H0 critical-path expectation (3 → 2 open requirements under the emulated profile). Updated `tests/test_release_minimum_manifest.py`; receipt: `provenance/evidence/d62bf2719f7bbe9fc59ad010459265169a76378a941b3298db4f8ccd3078ce88.json`.

Partitioned test execution results: architecture/component/contracts/governance (51 tests) passed in 11.1s; first application batch (38 tests) passed in 5.4s; governance/audit batch (34 tests) passed in 20.1s; contract/domain batch (84 tests) passed in 34.6s; integration/privacy batch passed in 16.2s; final storage/web batch (75 tests) passed in 9.6s. The release/qualification batch exposed only the corrected two-open-requirement expectation and passed its focused corrected test afterward. The monolithic `test-all` command remains operationally slow and has not been claimed as completed evidence.

Complete offline verification and claims closure now pass.

Exact commands:

```text
.venv\Scripts\python.exe scripts/dev.py verify
.venv\Scripts\python.exe scripts/dev.py claims
```

Receipts:

- `provenance/evidence/5c53a843f6752a08ccc9d064a6a2507e56dd40014fd175e54a718d6d615bfac5.json`
- `provenance/evidence/125878b53763d960aeed9b3834d46a2a8cabc574df4c6a5860eedb3c6077ca09.json`

The gate command itself remains bounded by the full-suite runtime and timed out; no pass is claimed for `scripts/dev.py gates`.

Reran the complete G0 gate lane with a 300-second execution bound. It passed after 147 seconds, including the expensive release-candidate tests. Receipt: `provenance/evidence/016864208e926818e4f8a9cfabc3e1dec4bd082655cc2d70863fd038c90c6e3c.json`.

## Collaborative Detection contracts and build-plan adoption — SE-COLLAB-CODEX-001

Adopted the proposed collaborative-detection extension as an optional H1/S8 workstream. Added disabled-by-default contract schemas, privacy-minimized Pydantic models, hazard-scoped observation validation, consent safety (`research_enabled` requires `sharing_enabled`), offline command-catalog entries, and a phased implementation plan. No Gmail task, credential check, network transport, or incident writer was added; collaboration remains explicitly planned beyond the contract slice.

Changed paths:

- `schemas/collaboration/correlation-domain-v1.schema.json`
- `schemas/collaboration/collaborative-signal-v1.schema.json`
- `schemas/collaboration/collaboration-consent-v1.schema.json`
- `src/sentinel_edge/collaboration/__init__.py`
- `src/sentinel_edge/collaboration/models.py`
- `tests/test_collaboration_contracts.py`
- `architecture/command-catalog.yaml`
- `scripts/dev.py`
- `docs/DEVELOPMENT_PLAN.md`

Exact verification commands:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_collaboration_contracts.py
.venv\Scripts\python.exe scripts/validate_command_catalog.py
.venv\Scripts\python.exe scripts/check_architecture_boundaries.py
```

Receipt scope: development/fixture contract evidence only; this does not qualify Arm64 target execution, physical sensing, Gmail access, authenticated peers, or production collaborative incidents.

## Collaborative local signal factory and policy correlation — SE-COLLAB-CODEX-001 Phase 2/3

Added deterministic opt-in signal creation with pseudonymous node/episode identifiers, bounded expiry, research-consent propagation, hazard/domain validation, one-peer-per-episode accounting, clock-safety handling, and explicit `email_unverified` review-only behavior. Correlation returns a decision trace; it does not mutate incident state.

Additional changed paths:

- `src/sentinel_edge/collaboration/factory.py`
- `src/sentinel_edge/collaboration/policy.py`
- `tests/test_collaboration_policy.py`
- `config/collaboration.yaml`
- `architecture/collaboration-policy.yaml`
- `src/sentinel_edge/collaboration/demo.py`

Exact verification commands:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_collaboration_contracts.py tests/test_collaboration_policy.py
.venv\Scripts\python.exe -m pytest -q tests/test_multi_node_correlation.py tests/test_peer_security.py
.venv\Scripts\python.exe scripts/check_architecture_boundaries.py
.venv\Scripts\python.exe scripts/dev.py collaboration-demo
```

Receipt: `provenance/evidence/ebeda568839c33cca6a75c15edfc29e1ab21663326ec0c468d239e38285c5caf.json`.

## Absolute benchmark values with percentage deltas — REQ-CLM-004

Benchmark governance reports now include `percentage_delta` alongside absolute per-variant values and signed paired deltas. A regression proves the report cannot express an optimization claim using percentages alone.

Changed paths:

- `src/sentinel_edge/benchmark/governance.py`
- `tests/test_benchmark_governance_v018.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_benchmark_governance_v018.py --tb=short -W error::pytestUnraisableExceptionWarning
```

## No-silent-skips acceptance gate — REQ-CON-005

Expanded the deterministic no-silent-skips regression to cover xfail/xpass log markers and collection-error XML results. The existing gate rejects skipped, failed, errored, deselected, rerun, xfailed and xpassed acceptance evidence.

Changed paths:

- `tests/governance/test_no_silent_skips.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\governance\\test_no_silent_skips.py --tb=short -W error::pytestUnraisableExceptionWarning
```

## Fail-closed mandatory test lane — REQ-CON-004

Added `mandatory_test_command`, which rejects an empty test selection before invoking pytest. The development workstream lane now uses this helper, and the controlled zero-test case is covered by a regression.

Changed paths:

- `scripts/dev.py`
- `tests/test_i00_dev_commands.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_i00_dev_commands.py --tb=short -W error::pytestUnraisableExceptionWarning
```

## Backfill event-time preservation — REQ-BKF-001

Added explicit `AnalysisResult.event_time` propagation from the source observation and made incident creation preserve event time separately from later acceptance time. The regression proves a recovered old record cannot appear newly observed solely because fetch/acceptance occurred later.

Changed paths:

- `src/sentinel_edge/domain/models.py`
- `src/sentinel_edge/analysis/service.py`
- `src/sentinel_edge/incidents/engine.py`
- `tests/test_incidents.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_incidents.py --tb=short -W error::pytestUnraisableExceptionWarning
```

## Generated-prose independence — REQ-AIT-002

Added a regression proving an untrusted descriptive string has no path into the authoritative incident state: the engine commits only the typed analysis result and preserves its state independently of prose.

Changed paths:

- `tests/test_hazards.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Client REST boundary and persistence isolation — REQ-CMP-009

Added a client-surface regression rejecting database, filesystem/persistence, internal-transport, and credential-storage markers. The semantic client is required to use the versioned REST surface and omit browser credential credentials from fetch requests.

Changed paths:

- `tests/test_client_security.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_client_security.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Versioned REST/OpenAPI boundary — REQ-CMP-008

Added an integration regression that enumerates all schema-visible application routes, requires supported operations to use `/v1/`, and verifies that the route set is represented in the generated OpenAPI contract with both read and write operations.

Changed paths:

- `tests/test_api.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_api.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Collector acquisition boundary — REQ-CMP-002

Added an architecture regression that scans executable source for connector/acquisition imports and permits them only in the collector boundary (with the existing release network-observation exception). Hidden connector dependencies in analyzer, runtime, incident, gateway, and client components now fail the test.

Changed paths:

- `tests/test_architecture.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_architecture.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Component ownership and single-writer policy — REQ-CMP-014

Added a regression over `architecture/owned-namespaces.yaml` that asserts one incident lifecycle authority and unique ownership keys for every critical database, artifact, and secret namespace.

Changed paths:

- `tests/test_architecture.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_architecture.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Scoped projection cursors — REQ-CUR-001, REQ-CUR-002

Bound projection cursors to a principal/filter scope digest in addition to stream epoch and authority/projection versions. Continuity now rejects another principal or filter as `resync_required`; cursor contents remain non-authoritative because REST snapshots are rebuilt from the incident engine’s current authoritative state.

Changed paths:

- `src/sentinel_edge/projections/service.py`
- `src/sentinel_edge/gateway/api.py`
- `tests/test_live_projections_and_offline.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_live_projections_and_offline.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Plugin graph and lifecycle validation — REQ-PLG-003

Added deterministic dependency-graph validation that rejects unknown dependencies and cycles, plus a closed plugin lifecycle transition table that rejects illegal transitions. Malicious-manifest regressions cover both failure modes.

Changed paths:

- `src/sentinel_edge/operations/plugins.py`
- `src/sentinel_edge/operations/__init__.py`
- `tests/test_plugin_boundaries.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_plugin_boundaries.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Typed plugin authority boundary — REQ-PLG-001, REQ-PLG-002

Added an allowlisted typed plugin capability manifest. Unknown/free-form capabilities are rejected, and incident lifecycle authority is reserved to the `incident` plugin so non-Incident plugins cannot obtain Component 4 authority.

Changed paths:

- `src/sentinel_edge/operations/plugins.py`
- `src/sentinel_edge/operations/__init__.py`
- `tests/test_plugin_boundaries.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_plugin_boundaries.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Normal scheduling policy — REQ-OSS-001

Recorded the scheduler policy explicitly in `SchedulerSnapshot`, defaulting to normal scheduling. Added a regression proving no real-time scheduling policy is implicitly required by the runtime scheduler.

Changed paths:

- `src/sentinel_edge/domain/models.py`
- `tests/test_clock_and_overload.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Removed ArmNN provider boundary — REQ-RUN-001

Added a deterministic runtime/configuration scan that rejects the removed ArmNN execution-provider path, with a regression over executable source material. Contract documentation remains excluded from the scan because it records the authoritative decision rather than runtime configuration.

Changed paths:

- `src/sentinel_edge/qualification/runtime_execution.py`
- `src/sentinel_edge/qualification/__init__.py`
- `tests/test_clock_and_overload.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Offline judge fixture bundle — REQ-DAT-006

Added a deterministic fixture-bundle verifier covering the required scenario, camera, model and sensor inputs. It rejects missing files and network URI markers, keeping the judge path explicitly offline.

Changed paths:

- `src/sentinel_edge/qualification/fixtures.py`
- `src/sentinel_edge/qualification/__init__.py`
- `tests/test_clock_and_overload.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## Earthquake IMU window and waveform closure — REQ-EQ-001, REQ-EQ-005

Added fixed-rate IMU window partitioning that preserves sequence and timing gaps as explicit metadata, plus deterministic complete/incomplete window tests. Existing bounded trigger-clip retention is now covered alongside the fixed-rate waveform path; no physical-device qualification is claimed.

Changed paths:

- `src/sentinel_edge/qualification/sensors.py`
- `src/sentinel_edge/qualification/__init__.py`
- `tests/test_clock_and_overload.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```

## UX contract closure — REQ-UX-001, REQ-UX-010

Promoted the four-hazard desktop overview and persistent research-only warning. The client regression asserts all four hazard identities are rendered together; export manifests now carry the same research warning so it survives export boundaries.

Changed paths:

- `src/sentinel_edge/exports/service.py`
- `tests/test_client_security.py`
- `tests/test_artifacts_and_claims.py`
- `registries/requirements.yaml`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_COVERAGE.md`
- `docs/OPEN_BLOCKERS.md`
- `tests/test_conformance_ledger.py`

Exact verification commands:

```text
.venv\\Scripts\\python.exe -m pytest -q tests\\test_client_security.py tests\\test_artifacts_and_claims.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning
```
- Promoted `REQ-UX-002` to `IMPLEMENTED`: the semantic client keeps the dedicated system-health region structurally separate from the hazard-results region.
- Changed paths: `tests/test_client_security.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_client_security.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (1 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-UX-003` to `IMPLEMENTED`: the semantic client exposes scheduler activity in system health and distinguishes idle from serving hazard projections.
- Changed paths: `tests/test_client_security.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_client_security.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (1 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-UX-005` to `IMPLEMENTED`: the semantic client visibly renders signal freshness with an explicit unknown fallback, preserving missing/stale signal visibility.
- Changed paths: `tests/test_client_security.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_client_security.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (1 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-UX-004` to `IMPLEMENTED`: the semantic client renders every incident card’s stored decision reasons under an explicit `Why` field, with a contract test covering the reason-code path.
- Changed paths: `tests/test_client_security.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_client_security.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (1 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-DAT-008` to `IMPLEMENTED`: evidence records now expose a nonblank `authority_role` separately from `source_standing`, with API coverage proving the distinction is visible.
- Changed paths: `src/sentinel_edge/domain/models.py`, `tests/test_evidence_api.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_evidence_api.py tests\\test_evidence_lifecycle_api.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (6 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-DAT-002` to `IMPLEMENTED`: the analysis boundary enforces a 5-second source TTL, forcing stale observations to zero score/normal state and recording `source_ttl_expired_zero_contribution`.
- Changed paths: `src/sentinel_edge/analysis/service.py`, `tests/test_hazards.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (11 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-EVT-004` to `IMPLEMENTED`: incident records now carry append-only `confirm`, `reject`, `uncertain`, or `control` labels; each analysis extends the label audit without rewriting prior journal entries.
- Changed paths: `src/sentinel_edge/domain/models.py`, `src/sentinel_edge/incidents/engine.py`, `tests/test_incidents.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_incidents.py tests\\test_incident_commands_and_relations.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (10 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-EVT-003` to `IMPLEMENTED`: analysis and incident records now preserve source lineage, model profile, and configuration-hash bindings through the Component 2 → Component 4 path.
- Changed paths: `src/sentinel_edge/domain/models.py`, `src/sentinel_edge/analysis/service.py`, `src/sentinel_edge/incidents/engine.py`, `tests/test_incidents.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_incidents.py tests\\test_incident_commands_and_relations.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (9 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-LS-006` to `IMPLEMENTED`: landslide analysis recommends a bounded cadence multiplier of 2.0 only when fresh rainfall/seismic context is elevated, otherwise retaining baseline cadence.
- Changed paths: `tests/test_flood_landslide_contracts.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_flood_landslide_contracts.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (6 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-EQ-009` to `IMPLEMENTED`: earthquake analysis exposes clock epoch/health and caps auto-confirmation when the clock is in an unsafe discontinuity epoch.
- Changed paths: `src/sentinel_edge/hazards/earthquake.py`, `tests/test_hazards.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (10 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-EQ-008` to `IMPLEMENTED`: earthquake public summaries use observed-motion wording and have a regression rejecting prediction/forecast language.
- Changed paths: `src/sentinel_edge/hazards/earthquake.py`, `tests/test_hazards.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (9 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-WF-008` to `IMPLEMENTED`: wildfire localization emits only a normalized camera-sector index and explicitly records `camera_sector_only`; no latitude/longitude is produced.
- Changed paths: `src/sentinel_edge/hazards/wildfire.py`, `tests/test_hazards.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (8 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-WF-005` to `IMPLEMENTED`: added a bounded trigger clip buffer retaining the latest pre-trigger window and an exact post-trigger window, with explicit completeness state.
- Changed paths: `src/sentinel_edge/runtime/clip.py`, `src/sentinel_edge/runtime/__init__.py`, `tests/test_clock_and_overload.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (7 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-WF-004` to `IMPLEMENTED`: wildfire confirmation requires temporal persistence, with a deterministic regression proving a single positive frame cannot confirm smoke.
- Changed paths: `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (7 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-WF-003` to `IMPLEMENTED`: the wildfire Stage-2 deterministic detector records a bounded region score, normalized region center, and local latency alongside Stage-1 output.
- Changed paths: `src/sentinel_edge/hazards/wildfire.py`, `tests/test_hazards.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (7 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-WF-002` to `IMPLEMENTED`: the deterministic wildfire Stage-1 path now exposes score, bounded uncertainty, and measured local latency in the analysis feature record.
- Changed paths: `src/sentinel_edge/hazards/wildfire.py`, `tests/test_hazards.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_hazards.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (6 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-ORC-005` to `IMPLEMENTED`: development orchestration can reallocate future workload cadence from fresh evidence/context, bounds the multiplier, and records a deterministic `cadence_reallocated:<reason>` code.
- Changed paths: `src/sentinel_edge/runtime/scheduler.py`, `tests/test_clock_and_overload.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (6 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-ORC-004` to `IMPLEMENTED`: flood and landslide workloads are both admitted after their bounded deferral under sustained overload, preventing starvation.
- Changed paths: `tests/test_clock_and_overload.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (5 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-ORC-003` to `IMPLEMENTED`: wildfire Stage-2 forced-scan cadence is admitted at its deadline under overload, despite a longer general deferral budget, and records `forced_scan_due`.
- Changed paths: `tests/test_clock_and_overload.py`, `registries/requirements.yaml`, implementation-status/coverage/blocker/traceability projections, generated qualification ledgers, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_clock_and_overload.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (4 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid after receipt refresh).
- Promoted `REQ-EVT-001` to `IMPLEMENTED`: hazard-specific incident identities and current-state indexing are covered by a regression proving wildfire and earthquake aggregates cannot collide.
- Changed paths: `tests/test_incidents.py`, `registries/requirements.yaml`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `tests/test_conformance_ledger.py`, `registries/evidence.yaml`, generated qualification ledgers, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_incidents.py tests\\test_incident_commands_and_relations.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (8 passed); projection generators; `validate_evidence_registry.py`; `validate_conformance_ledger.py` (both valid).
- Added a Component 4 replay regression: re-delivering an analysis with the same identity cannot alter its state, advance the incident version, or append a second journal entry. `REQ-CAU-001` and `REQ-CAU-002` remain open because this proves replay idempotence but not the full out-of-order/concurrent acceptance matrices.
- Changed paths: `tests/test_incidents.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_incidents.py tests\\test_incident_commands_and_relations.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (7 passed).
- Audited `REQ-ART-002` as an H1 privacy requirement rather than counting it as H0 progress; existing restricted-evidence API coverage redacts claim/source/digest metadata. Corrected the implementation-status narrative from stale `119` to the authoritative `110` open H0 requirements.
- Changed paths: `docs/IMPLEMENTATION_STATUS.md`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `Select-String -Path registries\\requirements.yaml -Pattern 'REQ-ART-002' -Context 0,18`; `rg -n "restricted|content_sha256|disposition_restricted" tests -g "*.py"`.
- Promoted `REQ-ART-001` to `IMPLEMENTED`: artifact references use opaque SHA-256 bindings, export member paths are archive-relative, and absolute, Windows drive-qualified, backslash, and traversal paths are rejected. Artifact/export/API tests passed 8 tests.
- Changed paths: `src/sentinel_edge/exports/service.py`, `tests/test_artifact_reference_contract.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_artifact_reference_contract.py tests\\test_privacy_export_api.py tests\\test_artifacts_and_claims.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (8 passed); `.venv\\Scripts\\python.exe scripts\\generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts\\generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts\\generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts\\generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts\\generate_deferred_risk_registers.py`.
- Corrected the implementation-status report to match the authoritative requirements registry: 287 total requirements are `IMPLEMENTED`; H0 remains 129 implemented and 111 open. Regenerated deferred-risk projections and reran evidence, conformance, architecture, and offline verification successfully.
- Changed paths: `docs/IMPLEMENTATION_STATUS.md`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts\\generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts\\validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts\\validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts\\dev.py verify`.
- Promoted `REQ-AZF-002` to `IMPLEMENTED`: the authoritative command catalog requires every command to declare `point_in_time`, `revalidate_before_commit`, or `user_reconfirm` semantics, and mutation/zero-work tests reject invalid or undocumented catalog entries. `REQ-AZF-003` remains open pending cross-operation delayed-command evidence.
- Changed paths: `registries/requirements.yaml`, `tests/test_command_catalog.py`, `tests/test_i00_dev_commands.py`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `registries/evidence.yaml`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_command_catalog.py tests\\test_i00_dev_commands.py tests\\test_incident_commands_and_relations.py tests\\test_live_projections_and_offline.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (18 passed); `.venv\\Scripts\\python.exe scripts\\generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts\\generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts\\generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts\\generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts\\generate_deferred_risk_registers.py`.

- Promoted `REQ-DLV-004` to `IMPLEMENTED`: the incident list now emits `X-Incident-Authority` and `X-Incident-Projection` headers, explicitly distinguishing unavailable authority and authoritative-stale projections from current authority. Focused authority/storage tests passed 10 tests.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_storage_api.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_storage_api.py tests\\test_authority_watermark_closure.py tests\\test_authority_journal_conformance.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (10 passed); `.venv\\Scripts\\python.exe scripts\\generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts\\generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts\\generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts\\generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts\\generate_deferred_risk_registers.py`.

## 2026-08-11

- Reconciled the v0.22 master building plan with the active registries and contract files.
- Added offline development commands for setup, doctor, demo, scenario, benchmark, benchmark-replay, claims, and AER.
- Made `python scripts/dev.py setup` execute deterministic registry, ADR, version, and architecture checks.
- Added the Judge Guide and documented the fixture/target evidence boundary.
- Fixed injected network-namespace probe evaluation on hosts without Linux `unshare`.
- Normalized the release lock file to LF line endings.

## Evidence status

The repository remains a development candidate. Physical Raspberry Pi/Arm64 qualification, physical sensor capture, target runtime/model execution, field commissioning, measured target benchmarks, and independent reviews remain open until receipt-backed evidence is available.

## 2026-08-12 continuation

- Fixed Windows scenario-engine finalization so SQLite resources close before temporary artifact directories are reclaimed; this removes unraisable `WinError 32` cleanup warnings for direct-use engines.
- Added the full warning-strict 319-test receipt `EV-R00-FULL-SUITE-20260812` and refreshed the generated conformance ledger, release checklist, release minimum manifest, baseline receipt, and release candidate.
- Changed paths: `src/sentinel_edge/scenario/engine.py`, `scripts/dev.py`, `tests/test_evidence_registry.py`, `tests/test_audit_baseline.py`, `registries/evidence.yaml`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/release-minimum-manifest.json`, `provenance/evidence/1e51a40279e6e95cf36d1509598f639037acb644ee2e802a5b7b3b1547e1a02d.json`, `provenance/evidence/remediation/R00/baseline-receipt.json`, `release-candidate.json`, `release-candidate.json.sig.json`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `python scripts/dev.py verify`; `python scripts/dev.py gates`; `python scripts/validate_ci_workflows.py`; `python scripts/check_lock_metadata.py`; `python scripts/check_contract_sync.py`; `python scripts/repository_hygiene.py --check`.
- Restored the explicit `test-arm` command required by `.github/workflows/ci-arm.yml`; it is a successful planned-lane guard and states that it is not benchmark evidence. The command catalog now contains 39 entries and `tests/test_command_catalog.py` covers its presence.
- Added `scripts/validate_traceability.py` and `tests/test_traceability.py`; every H0 requirement must have implementation-task and verification-test mappings plus an explicit evidence disposition. Wired the validator into `dev.py verify` and `dev.py gates`.
- Added generated `qualification/scope-freeze.json` plus `scripts/generate_scope_freeze.py`, `scripts/validate_scope_freeze.py`, and `tests/test_scope_freeze.py`. The frozen 240-item H0 cutline now detects registry drift and requires complete exception fields for any post-freeze change; the validator runs in both standard lanes.
- Added generated `qualification/deferred-debt-register.json` and `qualification/residual-risk-register.json` from the authoritative uncertainties and open-blockers sources, with rationale, dependency, safe limitation, owner and status fields. Added generation/validation scripts and a gate test; current projections contain 4 deferred uncertainties and 17 residual risks.
- Fixed Windows atomic restore replacement by retrying transient `PermissionError` after SQLite resources close; focused regression passed.
- Added full warning-strict 323-test receipt `EV-R00-FULL-SUITE-R01-20260812` at `provenance/evidence/b7c72e22a43392d8e3a9975359952eb4f1e74300d7235095d38507583bb7d51d.json` (SHA-256 `47d4556ed844d3c6a2ecd85db6a46fdafa7c8dcbb3e9bb0cf1cffca1b36bb8257`, 354.1 seconds).
- Changed paths: `src/sentinel_edge/storage/backup.py`, `registries/evidence.yaml`, `tests/test_evidence_registry.py`, `tests/test_audit_baseline.py`, `qualification/conformance-ledger.json`, `qualification/release-minimum-manifest.json`, `provenance/evidence/b7c72e22a43392d8e3a9975359952eb4f1e74300d7235095d38507583bb7d51d.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_privacy_backup_and_exports.py::test_pre_deletion_backup_reapplies_newer_tombstone_before_readiness --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `python scripts/generate_conformance_ledger.py`; `python scripts/generate_release_minimum_manifest.py`.
- Strengthened `python scripts/dev.py verify` to enforce version consistency, offline lock metadata, contract/registry synchronization, capability-state validation, and repository hygiene in the standard deterministic lane. These checks independently pass on the current worktree.
- Changed paths: `scripts/dev.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `python scripts/validate_capability_status.py`; `python scripts/check_version_consistency.py`; `python scripts/check_lock_metadata.py`; `python scripts/check_contract_sync.py`; `python scripts/repository_hygiene.py --check`.
- Applied the same identity, synchronization, capability-state and lock checks to `python scripts/dev.py gates`, keeping the release gate lane aligned with repository verification.
- Added a regression test requiring those checks to remain present in both standard lanes.
- Changed paths: `tests/test_i00_dev_commands.py`.
- Re-ran the complete warning-strict suite after the delivery-lane coverage change: 324 tests passed in 279.4 seconds. Registered `EV-R00-FULL-SUITE-R02-20260812` at `provenance/evidence/61f0a710bbe421946ffa2b86bc7fad8c9aa527603bba62991cc30edd9f45302f.json` with SHA-256 `79f61e34f3a14cff2c6298206027bb82bf2aa913c884e27901c18ab8a51e92a3`.
- Refreshed the evidence registry count to 366, conformance ledger, release minimum manifest, baseline receipt and release candidate; candidate verification has no inventory differences.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `python scripts/generate_conformance_ledger.py`; `python scripts/generate_release_minimum_manifest.py`; `python scripts/audit_baseline.py --output provenance/evidence/remediation/R00/baseline-receipt.json`; `python -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `python -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`.
- Added generated `qualification/g0-gate-status.json`, sourced from the active v0.22 contract’s twelve named packs and the H0 release-minimum manifest. It reports all twelve packs as `blocked` while release admission is false, rather than collapsing status into generic `e2e/integration/static` labels. Added generation, validation, and regression coverage; registered `EV-R00-G0-GATE-STATUS-20260812` with SHA-256 `2f0bd7400a64e40801c104aa76e5215ba4ba5574ea3ac959b63c2876b633d7f7`.
- Changed paths: `scripts/generate_g0_gate_status.py`, `scripts/validate_g0_gate_status.py`, `qualification/g0-gate-status.json`, `tests/test_g0_gate_status.py`, `scripts/dev.py`, `registries/evidence.yaml`, `tests/test_evidence_registry.py`, `tests/test_audit_baseline.py`, `qualification/conformance-ledger.json`, `qualification/release-minimum-manifest.json`, `provenance/evidence/remediation/R00/baseline-receipt.json`, `release-candidate.json`.
- Exact verification commands: `python scripts/generate_g0_gate_status.py`; `python scripts/validate_g0_gate_status.py`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_g0_gate_status.py tests/test_i00_dev_commands.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `python scripts/dev.py verify`; `python scripts/generate_conformance_ledger.py`; `python scripts/generate_release_minimum_manifest.py`; `python scripts/audit_baseline.py --output provenance/evidence/remediation/R00/baseline-receipt.json`; `python -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `python -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`.
- Corrected G0 status values to the contract-defined vocabulary: failing packs now report `fail` rather than the non-contract `blocked` label. Updated the registered artifact digest to `12ab9c701a7d1be1c46f29b6c7863c9f04a671bacb7f1c0a2c2a3a6b9c3fed72`.
- Bound the twelve-pack G0 status summary and artifact digest into release-candidate identity and admission. Candidate verification now rejects an invalid/missing G0 pack set or any non-passing pack from release admission; release-candidate tests pass.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py` (verification-only coverage exercised), `release-candidate.json`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_release_candidate.py tests/test_g0_gate_status.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `python -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `python -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`; `python scripts/dev.py gates`.
- Added semantic G0 binding checks to `verify_release_candidate`, so candidate verification validates the current twelve-pack artifact’s schema, IDs, statuses, summary and digest in addition to inventory identity.
- Re-ran the complete warning-strict suite after this candidate-verifier change: 326 tests passed in 309.2 seconds. Registered `EV-R00-FULL-SUITE-R03-20260812` at `provenance/evidence/5c85189971115aaad16f374e036f61c0f73ec74c0fda358a0d2f36e996576ab9.json` with SHA-256 `eead7ec1620364a2c1ac40327e8f7b43cf855b84fdc6de6043bc0c15eda10b2f`.
- Corrected the G0 validator to read the existing projection before generating the expected projection, and added mutation coverage proving drift is rejected. The current pinned-venv warning-strict suite passed 328 tests in 307 seconds (known dependency/cache warnings; no unraisable warnings). The final current receipt is registered as `EV-R00-FULL-SUITE-R04-20260812` at `provenance/evidence/03e8e508a8195124fe5069864285563ff0b289f13c06a86fa2f9bfd06b227b4c.json` with SHA-256 `36f927467ec45450c1d8502e519a2a7314f91ea25309e03c5f6034e17f477adf`.
- Strengthened the planned Arm CI lane: `python scripts/dev.py test-arm` now runs the deterministic doctor/host inspection before declaring the lane non-target evidence, and added a regression test for that contract. Focused command passed 6 tests; the Windows development host was correctly reported as `development_host_only` with `target_device_claim_allowed: false`.
- Changed paths: `scripts/dev.py`, `tests/test_i00_dev_commands.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_i00_dev_commands.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/dev.py test-arm`.
- Extended the G0 projection to resolve every named pack to H0 requirement IDs, registry test IDs and source/evidence artifact references using the authoritative technical contract and release-minimum manifest. Updated the bound G0 artifact digest to `084ec3ac0901d8299233ebe304b6329fb91ce4bb514c694e6fc392f8279f84a4`. Focused G0/dev-command coverage passed 8 tests; evidence registry, conformance projections, candidate verification, `dev.py verify` and `dev.py gates` pass.
- Changed paths: `scripts/generate_g0_gate_status.py`, `tests/test_g0_gate_status.py`, `qualification/g0-gate-status.json`, `registries/evidence.yaml`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/validate_g0_gate_status.py`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_g0_gate_status.py tests/test_i00_dev_commands.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Audited the G0 mapping for phantom technical-contract IDs and restricted each pack's `requirements` list to IDs present in the authoritative H0 release manifest; the projection digest remained unchanged because the prior mapped IDs were already registry-backed. Re-ran evidence, projection, candidate, verify and gate validation successfully.
- Repeated the G0 mapping audit after projection regeneration, with a regression assertion that every mapped requirement is an `REQ-` registry identifier. Focused G0 coverage passed 2 tests; evidence registry, conformance projections, release candidate, `dev.py verify` and `dev.py gates` all passed.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/validate_g0_gate_status.py`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_g0_gate_status.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Hardened `scripts/validate_requirement_closure.py`: VERIFIED evidence must now be ACTIVE, carry a lowercase 64-hex SHA-256, resolve to an in-root file, and match its digest. Added an inactive-receipt regression test. Closure validation, focused tests (3 passed), `dev.py verify` and `dev.py gates` pass.
- Changed paths: `scripts/validate_requirement_closure.py`, `tests/test_i01_requirement_closure.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_i01_requirement_closure.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Hardened `scripts/validate_evidence_registry.py` against symlink/junction escapes by resolving local paths and requiring the resolved path to remain under the repository root. Added a fail-closed regression test; the combined evidence/closure suite passed 7 tests, the live registry remained valid, and both standard lanes passed.
- Changed paths: `scripts/validate_evidence_registry.py`, `tests/test_evidence_registry.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_evidence_registry.py tests/test_i01_requirement_closure.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Re-ran the complete warning-strict suite after the receipt-integrity changes: 335 tests passed in 250 seconds. Replaced the current `EV-R00-FULL-SUITE-R04-20260812` binding with `provenance/evidence/edbaaf02c0cb5ec62ba2d26a543652e9bbbbbd967038a499205c68b07ab2ec32.json` (SHA-256 `b776e4798b4687dcc0db09d89cdbb623fcd30337ee3578647b1f3548e57a2814`). Evidence registry, conformance projections, candidate verification, `dev.py verify` and `dev.py gates` pass.
- Changed paths: `provenance/evidence/edbaaf02c0cb5ec62ba2d26a543652e9bbbbbd967038a499205c68b07ab2ec32.json`, `registries/evidence.yaml`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q --tb=short -W error::pytest.PytestUnraisableExceptionWarning" --result passed --duration-seconds 250 --passed 335 --output-dir provenance/evidence`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Corrected G0 “all G0” technical-contract mapping semantics so `REQ-RSB-001`, `REQ-RSB-002` and `REQ-RSB-004` are included in every pack. All 240 H0 requirements now map to at least one G0 pack; focused G0 tests passed 2 tests. Refreshed the G0 digest to `cc92adf5639c228f9b4628bcb57b3340a7868f081efbbab5f72936d703ee31c4`.
- Re-ran the full warning-strict suite after projection synchronization: 335 tests passed in 416 seconds. Registered the current receipt at `provenance/evidence/d79048da82242e1cac950a3193c906131f897fe0d346289c40b482d75bea39d8.json` with SHA-256 `fa8aa062ff8708651554354d5546809019a5435fe87948fd8418c5b7165ae67e`. Evidence registry, conformance projections, `dev.py verify` and `dev.py gates` pass.
- Changed paths: `scripts/generate_g0_gate_status.py`, `tests/test_g0_gate_status.py`, `qualification/g0-gate-status.json`, `registries/evidence.yaml`, `provenance/evidence/d79048da82242e1cac950a3193c906131f897fe0d346289c40b482d75bea39d8.json`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `HACKATHON_WORKLOG.md`.
- Made G0 completeness fail closed in `validate_g0_gate_status.py`: it now independently compares the union of pack requirement IDs to the H0 release manifest and requires every pack to expose tests and artifacts. Added mutation coverage for an incomplete mapping; focused G0 tests passed 3 tests and both standard lanes passed.
- Changed paths: `scripts/validate_g0_gate_status.py`, `tests/test_g0_gate_status.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_g0_gate_status.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Hardened Claim Registry validation so every claim artifact reference must be a valid SHA-256 reference bound to one of the registry's source artifacts. Added a regression test for unregistered claim hashes; claim tests passed 4 tests, claim generation/validation passed, and both standard lanes passed.
- Changed paths: `scripts/validate_claim_registry.py`, `tests/test_claim_registry_generation.py`, `qualification/claim-registry.json`, `qualification/claim-table.md`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_claim_registry_generation.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/generate_claim_registry.py`; `.venv\\Scripts\\python.exe scripts/validate_claim_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Bound the generated Claim Registry digest and validity/count metadata into release-candidate identity; candidate verification now rejects Claim Registry mutation independently of inventory comparison. Release-candidate tests passed 6 tests, candidate verification passed with no inventory differences.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `release-candidate.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_release_candidate.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`.
- Strengthened candidate construction: Claim Registry validity now includes source-artifact existence/digest checks and claim-reference resolution, and release admission requires that semantic validity. Added a mutation regression; release-candidate tests passed 7 tests, candidate verification passed with no inventory differences, and both standard lanes passed.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `release-candidate.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_release_candidate.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Added explicit doctor diagnostics separating 64-bit development hosts from observed native Arm64 Linux and reporting missing physical-signal evidence. Added the target-evidence handoff procedure with exact target commands and receipt promotion rules; no target requirement was promoted without external evidence.
- Changed paths: `src/sentinel_edge/cli.py`, `tests/test_i00_dev_commands.py`, `docs/TARGET_EVIDENCE_HANDOFF.md`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_i00_dev_commands.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/validate_delivery_registry.py`.

- Hardened the gateway public error boundary: exception text is no longer copied into HTTP problem details; stable safe messages are returned while the original exception remains chained for private diagnostics. Offline reconfirmation keeps only its stable public classification. Requirement `REQ-ERR-001` remains open because the full acceptance evidence suite is not yet receipt-backed.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `rg -n "str\\(exc\\)" src\\sentinel_edge\\gateway\\api.py`; `C:\\Users\\angel.alvarez\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe -m compileall -q src\\sentinel_edge\\gateway\\api.py`; attempted API/security `pytest`, blocked by unavailable compatible `pydantic_core` in the workspace runtime.

- Added a deterministic regression scanner for the gateway public-problem boundary. It rejects direct exception-text serialization in public `message`/`detail` fields and verifies the safe message is constant. `REQ-ERR-001` remains CONFIRMED because this local static receipt does not prove the full public error corpus is free of secrets, raw upstream bodies, absolute paths, and stack text.
- Changed paths: `tests/test_public_problem_boundary.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_public_problem_boundary.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (2 passed); `rg -n "str\\(exc\\)" src\\sentinel_edge\\gateway\\api.py`.

- Closed a concrete filesystem-boundary leak in the authenticated artifact catalog: API records now use an explicit metadata allowlist and omit the owning store's `relative_path`; added an API regression assertion. `REQ-ARL-002` remains CONFIRMED pending execution of the full API acceptance lane.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_privacy_export_api.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m compileall -q src\\sentinel_edge\\gateway\\api.py`; `.venv\\Scripts\\python.exe -m pytest -q tests\\test_public_problem_boundary.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (2 passed); attempted `tests/test_privacy_export_api.py`, blocked by the workspace's incompatible `pydantic_core` binary.

- Promoted `REQ-ARL-002` to `IMPLEMENTED`: the artifact catalog now omits internal relative paths, export requests reject caller-supplied raw path fields, and the direct privacy/export API test passed. Also retained allowlisted `reconfirmation`/`stale` public classifications while suppressing raw exception text; the combined API/security slice passed 18 tests. H0 implementation-complete count is now 125 and open H0 count is 115.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_privacy_export_api.py`, `tests/test_incident_commands_and_relations.py`, `tests/test_live_projections_and_offline.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_privacy_export_api.py tests\\test_api.py tests\\test_auth_and_commands.py tests\\test_incident_commands_and_relations.py tests\\test_live_projections_and_offline.py tests\\test_storage_api.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (18 passed); `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify` (PASS); `.venv\\Scripts\\python.exe scripts/dev.py gates` (timed out after 300 seconds after progressing into the full test lane).

- Promoted `REQ-ERR-001` to `IMPLEMENTED` after hardening the gateway’s public error boundary. Raw exception text is suppressed, stable operational classifications remain allowlisted, and the public-problem/static plus secret-canary/API security suite passed 25 tests. H0 implementation-complete count is now 126 and open H0 count is 114; G0 remains not admitted because unrelated target/release evidence is still missing.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_public_problem_boundary.py`, `tests/test_disposition_and_secrets.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_public_problem_boundary.py tests\\test_disposition_and_secrets.py tests\\test_privacy_export_api.py tests\\test_api.py tests\\test_auth_and_commands.py tests\\test_incident_commands_and_relations.py tests\\test_live_projections_and_offline.py tests\\test_storage_api.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (25 passed); `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Promoted 17 repository-enforceable conformance, traceability, gate and release-scope requirements from `CONFIRMED` to `IMPLEMENTED`; this does not claim target qualification or `VERIFIED` evidence. Regenerated the conformance ledger, acceptance checklist and scope-freeze projection. H0 implementation-complete count is now 114 and open H0 count is 126.
- Changed paths: `registries/requirements.yaml`, `tests/test_conformance_ledger.py`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_g0_gate_status.py tests/test_release_candidate.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/validate_traceability.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/validate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Promoted the documented command-catalog controls `REQ-CMD-001` and `REQ-CMD-002` to `IMPLEMENTED` after command-catalog and development-command mutation coverage passed. Regenerated the release-minimum manifest and G0 projection; rebound `EV-R00-G0-GATE-STATUS-20260812` to `qualification/g0-gate-status.json` SHA-256 `e89ac84c69578c469c2923425a576aaf53dceb73a9d7fcb62c94a6ccf8baaf4a`. H0 implementation-complete count is now 116 and open H0 count is 124.
- Changed paths: `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_command_catalog.py tests/test_i00_dev_commands.py tests/test_conformance_ledger.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Synchronized implementation and blocker documentation with the authoritative registry: 273 total `IMPLEMENTED`, 116 H0 implemented and 124 H0 open. Regenerated deferred-debt and residual-risk projections after the documentation/registry update; the cumulative verification and G0 gates pass.
- Changed paths: `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Re-audited the remaining H0 runtime gaps before making further status changes; no new local implementation was promoted without a complete acceptance path. The cumulative verification lane initially found stale risk projections, which were regenerated; the final verification and G0 gates passed after the repair.
- Changed paths: `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Promoted `REQ-ARL-001` to `IMPLEMENTED`: artifact content has no public digest retrieval route, catalog access remains authorization-gated, and a guessed digest request returns 404 without content. Added the direct negative API assertion. H0 implementation-complete count is now 127 and open H0 count is 113.
- Changed paths: `tests/test_privacy_export_api.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests\\test_privacy_export_api.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning` (1 passed); `.venv\\Scripts\\python.exe scripts\\generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts\\generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts\\generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts\\generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts\\generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts\\validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts\\validate_conformance_ledger.py`.
- Promoted the repository-verifiable platform controls `REQ-PLT-005` through `REQ-PLT-008` (license, deterministic setup/doctor, hackathon work record, and source/input labeling) to `IMPLEMENTED`; target hardware and physical-signal qualification remain explicitly unverified. Regenerated all dependent projections and rebound the G0 projection receipt to SHA-256 `99b39f4272ac51ca722559c25110691ef26fabbdffefa7c15005295e310d3650`. H0 implementation-complete count is now 120 and open H0 count is 120.
- Changed paths: `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_command_catalog.py tests/test_i00_dev_commands.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Audited the next open URL/reference and source-policy requirements. The current repository has source qualification manifests but no server-side URL resolver, so no unsupported implementation promotion was made; the target/field blockers remain explicit rather than being paper-closed.
- Changed paths: `HACKATHON_WORKLOG.md`.
- Exact verification commands: `rg -n "ExternalReference|external_reference|canonical_url|url" src/sentinel_edge/gateway src/sentinel_edge/collector src/sentinel_edge/domain -g "*.py"`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Implemented the missing deterministic reference boundary in `sentinel_edge.collector.references`: HTTP(S)-only parsing, userinfo/fragment rejection, local/private/reserved literal rejection, canonicalization, default `reference_only` state, and explicit exact-host allowlisting for resolution admission. The module performs no network access and documents mandatory destination revalidation by the eventual connector.
- Changed paths: `src/sentinel_edge/collector/references.py`, `src/sentinel_edge/collector/__init__.py`, `tests/test_reference_policy.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Bound external-reference submission to connector source policy: `BoundedBackgroundConnector.submit_reference` now requires live mode plus an exact allowlist and routes every accepted URL through canonical reference validation; fixture/cached/simulated connectors cannot resolve external references. Added integration coverage; the combined reference/collector suite passed 8 tests and both standard lanes passed.
- Changed paths: `src/sentinel_edge/collector/connectors.py`, `src/sentinel_edge/collector/references.py`, `src/sentinel_edge/collector/__init__.py`, `tests/test_reference_policy.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py tests/test_collector.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Added typed `ConnectorMode` (`poll`, `subscribe`, `webhook`, `stream`, `fixture`) and made every bounded connector carry an explicit transport declaration. Connector reference submission remains routed through Component 1 policy; promoted `REQ-CNX-001` to `IMPLEMENTED`. Regenerated projections and rebound the G0 receipt to SHA-256 `9fe35960c9e1e93a2a93ad9b4f72eb8db6fb803bcdf72da249dc615fafdac9dd`. H0 implementation-complete count is now 121 and open H0 count is 119.
- Changed paths: `src/sentinel_edge/collector/connectors.py`, `src/sentinel_edge/collector/__init__.py`, `tests/test_reference_policy.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py tests/test_collector.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Added typed connector transport modes (`poll`, `subscribe`, `webhook`, `stream`, `fixture`) and explicit mode storage on every bounded connector. Promoted `REQ-CNX-001` to `IMPLEMENTED`; focused reference/collector tests passed 9 tests. Regenerated conformance, scope-freeze, release-minimum, G0, and deferred-risk projections; final `verify` and `gates` passed. H0 implementation-complete count is 121 and open H0 count is 119.
- Changed paths: `src/sentinel_edge/collector/connectors.py`, `src/sentinel_edge/collector/__init__.py`, `tests/test_reference_policy.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py tests/test_collector.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Added a normalization hook to every bounded connector; submissions are normalized before queueing and normalization failures are rejected without entering the worker. Promoted `REQ-CNX-002` to `IMPLEMENTED`; focused reference/collector plus connector-lifecycle tests passed 18 tests. H0 implementation-complete count is now 122 and open H0 count is 118.
- Changed paths: `src/sentinel_edge/collector/connectors.py`, `tests/test_reference_policy.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py tests/test_audit_revocation_and_connector_lifecycle.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Completed the connector normalization boundary: every submission passes through the configured Component 1 normalizer before queueing, and normalization exceptions are fail-closed. Promoted `REQ-CNX-002` to `IMPLEMENTED`; final cumulative verification and G0 gates passed after regenerating conformance and risk projections. H0 implementation-complete count is 122 and open H0 count is 118.
- Changed paths: `src/sentinel_edge/collector/connectors.py`, `tests/test_reference_policy.py`, `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py tests/test_audit_revocation_and_connector_lifecycle.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Promoted `REQ-REF-001` and `REQ-REF-002` to `IMPLEMENTED`: the reference validator, connector admission, and resolved-address revalidation now provide deterministic reference-only and SSRF/local-network controls with regression evidence. Regenerated projections and rebound the G0 receipt to SHA-256 `cfc19141651cb679b49149f5b8c1f93c7ba48852e47178cf300d14d02fb64965`. H0 implementation-complete count is now 124 and open H0 count is 116.
- Changed paths: `registries/requirements.yaml`, `registries/evidence.yaml`, `tests/test_conformance_ledger.py`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/OPEN_BLOCKERS.md`, `docs/TRACEABILITY_SUMMARY.md`, `qualification/conformance-ledger.json`, `qualification/release-acceptance-checklist.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py tests/test_audit_revocation_and_connector_lifecycle.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Strengthened the reference boundary with `validate_resolved_addresses`, which rejects empty DNS results, non-IP resolver output, and any unsafe address in the complete result set before connection. Added regression coverage for mixed public/private results and IPv4/IPv6 normalization; focused tests passed 5 tests and both standard lanes passed.
- Changed paths: `src/sentinel_edge/collector/references.py`, `src/sentinel_edge/collector/__init__.py`, `tests/test_reference_policy.py`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_reference_policy.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Made candidate verification fail closed when the bound Claim Registry is semantically invalid, even when its digest matches the candidate. Added regression coverage; release-candidate tests passed 9 tests, candidate verification returned `valid: true` with no inventory differences, and both standard lanes passed.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `release-candidate.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_release_candidate.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Closed the candidate claim-payload bypass: candidate identity now always uses the validated Claim Registry claims and rejects caller-supplied claim lists that differ. Added regression coverage; release-candidate tests passed 8 tests, candidate verification passed with no inventory differences, and both standard lanes passed.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `release-candidate.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv\\Scripts\\python.exe -m pytest -q tests/test_release_candidate.py --tb=short -W error::pytest.PytestUnraisableExceptionWarning`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli build-release-candidate --root . --state-dir .tmp/release-candidate-state --output release-candidate.json`; `.venv\\Scripts\\python.exe -m sentinel_edge.cli verify-release-candidate release-candidate.json --root .`; `.venv\\Scripts\\python.exe scripts/dev.py verify`; `.venv\\Scripts\\python.exe scripts/dev.py gates`.
- Added receipt-backed implementation evidence for `REQ-IN-008` (MQTT/local HTTP/WebSocket ingress adapter boundary); the focused ingress, reference-policy, collector and domain suite passed 18 tests. This remains development/fixture evidence and does not claim physical sensor qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/e67009d6aa205937dd038fbc140fc05dbe41b8650218fa391fb7bb1d7545213f.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_ingress_adapters.py tests/test_reference_policy.py tests/test_collector.py tests/test_domain.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-IN-009` (Android sensor bridge validation and collector normalization); the focused bridge/ingress/collector/domain suite passed 13 tests. This remains development evidence and does not claim physical sensor qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/20db8edc0a1496d68cc80b872ca5b7eb174318a3c63ae6eed2dde8e286a2d7df.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_android_sensor_bridge.py tests/test_ingress_adapters.py tests/test_collector.py tests/test_domain.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-WF-007` (controlled activity audit and incident idempotency); the focused controlled-activity, incident-command and authorization suite passed 14 tests. This is development evidence and does not claim field operation.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/48d2b4c7b36ca1ace8cd5be7be87a20ce382df605235d3bf6a7c8907f2749e1a.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_controlled_activity.py tests/test_incident_commands_and_relations.py tests/test_auth_and_commands.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-FL-004` (forecast horizon/uncertainty transparency and deterministic fallback); the focused forecast/flood/landslide suite passed 24 tests. This is development evidence and does not claim field calibration.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/ff7f1c9f5f296cc3c6ea4eae1fcd749a2af5c6a418c1c7fd78be84014435f1f8.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_forecast_transparency.py tests/test_flood_landslide_contracts.py tests/test_hazards.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-EQ-004` (earthquake hard-negative handling and deterministic abstention); the focused earthquake/hazard/threshold suite passed 20 tests. This is development evidence and does not claim target model-quality qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/95ceb7b2e8bfc447f10f1649706e258483c0e06609e77617062cb3d92773737d.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_earthquake_hard_negatives.py tests/test_hazards.py tests/test_threshold_abstention.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-EQ-006` (bounded deterministic multi-node earthquake correlation); the focused multi-node/earthquake/hazard suite passed 19 tests. This is development fixture evidence and does not claim field multi-node qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/2294ec565d808cfaa16ad750e50cde15eefdd636a0e2a9a85a147ae02aeaab3b.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_multi_node_correlation.py tests/test_earthquake_hard_negatives.py tests/test_hazards.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-EQ-007` (deterministic post-event earthquake corroboration and external matching); the focused post-event/multi-node/hard-negative suite passed 6 tests. This is development fixture evidence and does not claim live authority matching.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/d65612d85d431811ff62ebcbed78aacdb4da8c6dfcd7cfb039adca549d06e72f.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_post_event_corroboration.py tests/test_multi_node_correlation.py tests/test_earthquake_hard_negatives.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-IN-010` (bounded collector/sensor ring buffers with overwrite signaling); the focused collector/sensor/ingress suite passed 17 tests. This is development fixture evidence and does not claim physical signal qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/58ede227e2e5bad8dbaa7c934e4ff33588ddec5eef281a269242e95e7fe14d3e.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collector.py tests/test_sensor_plane.py tests/test_sensor_protocol.py tests/test_ingress_adapters.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-INT-001` (stable observation contract across HTTP, Android and sensor-plane adapters); the focused contract/ingress suite passed 11 tests. This is development fixture evidence and does not claim physical signal qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/d5e3f97018bcd260f5d16eea622a456994816f5220950c2cc48df18999a3923e.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_observation_contract_adapters.py tests/test_ingress_adapters.py tests/test_android_sensor_bridge.py tests/test_sensor_plane.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-INT-002` (SensorThings observation mapping); the focused SensorThings/contract suite passed 3 tests. This is development fixture evidence and does not claim external interoperability deployment.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/8de30e9d447dcec726bcfb00a853d2fbad1b6236482eaa1bcb000c4ccbfbab05.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_sensorthings_export.py tests/test_observation_contract_adapters.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-INT-003` (validated GeoJSON exchange boundary); the focused GeoJSON/geospatial/contract suite passed 8 tests. This is development fixture evidence and does not claim qualified datum or field geospatial deployment.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/7bf55001411937eb8b234504b2d7fb180c079ea1a08488600834ad38c20d5961.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_geojson_exchange.py tests/test_geospatial_contracts.py tests/test_observation_contract_adapters.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-INT-004` (CAP test-draft export with authority and privacy boundaries); the focused CAP/privacy/authority/export suite passed 16 tests. This is development fixture evidence and does not claim official warning authority.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/31a1b5c0a2fbb8eeef2c4a7bf38b88f2282e4325708e2ba7e719ff100f9cfd45.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_cap_test_drafts.py tests/test_privacy_backup_and_exports.py tests/test_authority_watermark_closure.py tests/test_public_export_scanner.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-INT-005` (bounded STAC metadata export); the focused STAC/SensorThings suite passed 3 tests. This is development fixture evidence and does not claim qualified external catalog deployment.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/86b3f6bc1e165dc50730acfbfa7be9b88c0a6002d39e776e51edc277139b3597.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_stac_metadata.py tests/test_sensorthings_export.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-001` (complete deterministic latency decomposition across the scenario path); the focused latency/scenario/fault/signature suite passed 6 tests. This is development fixture evidence and does not claim target timing qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/d769bfa6bd547cb2f293640a603d71d46161d147e5e5b9c7763f8e48f8fd1e38.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_latency_decomposition.py tests/test_scenario_e2e.py tests/test_capability_faults.py tests/test_signed_scenarios.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-002` (clock uncertainty metadata propagation through collection and recovery); the focused clock/collector/recovery/source-health suite passed 12 tests. This is development fixture evidence and does not claim qualified target time.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/acf4c27a12a8796a2f5055f3987a9e3249668c34e4d31536497595fa7fe4d5a4.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_clock_uncertainty_metadata.py tests/test_collector.py tests/test_recovery.py tests/test_source_health_lifecycle.py tests/test_domain.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-003` (stale replay rejection); the focused collector/recovery/Android/hazard suite passed 25 tests. This is development fixture evidence and does not claim target clock qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/87b3610157c7fc453e0d2fb04e90c9963ce4db9217a360eb85dbf900f1f0dccc.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collector.py tests/test_recovery.py tests/test_android_sensor_bridge.py tests/test_hazards.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-004` (versioned CRC sensor frames); the focused sensor protocol/Android/collector suite passed 14 tests. This is development fixture evidence and does not claim physical transport qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/47f1b5caaa93882ace97c9c443830b88f59aefceddb702331d5881e5d0ad679f.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_sensor_protocol.py tests/test_android_sensor_bridge.py tests/test_collector.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-005` (bounded validated sensor-plane ingestion); the focused sensor-plane/protocol/Android/collector suite passed 17 tests. This is development fixture evidence and does not claim physical sensor qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/98d1c903d503bbae1eed35016deefa1374b081e9a4b8593d02bbab5ca21362d9.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_sensor_plane.py tests/test_sensor_protocol.py tests/test_android_sensor_bridge.py tests/test_collector.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-006` (bounded authenticated external-trigger normalization); the focused trigger/sensor/collector suite passed 17 tests. This is development fixture evidence and does not claim field trigger qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/8b8a1eee38631ef7ea6f6f57a5ac234dca688cd1e877f2ee4af6cd5a8196c39a.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_external_trigger.py tests/test_sensor_plane.py tests/test_sensor_protocol.py tests/test_collector.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SEN-007` (bounded optional sensor-plane behavior with fail-closed unavailability); the focused optional-plane/sensor/trigger/collector suite passed 20 tests. This is development fixture evidence and does not claim physical sensor qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/1baef785e53b2b913e92b88859bbd288165e44bc711582dbd980f600eac8ee5b.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_sensor_plane_optional.py tests/test_sensor_plane.py tests/test_sensor_protocol.py tests/test_external_trigger.py tests/test_collector.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SCN-003` (deterministic reset, accelerated and step-through replay controls); the focused replay/scenario suite passed 3 tests. This is development fixture evidence and does not claim target runtime replay qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/c50fe997e9e64d3ea6a86d2abf510876eabf033fe7bbf3fe6721ad0eedb1bc17.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_scenario_replay_controls.py tests/test_scenario_e2e.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-SCN-004` (deterministic scenario fault injection and recovery); the focused fault/replay/scenario suite passed 5 tests. This is development fixture evidence and does not claim target fault qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/6ba535b8682fde053b0353212a80dd3d0551982bfcedf2a2388f4565c975e0d5.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_scenario_faults.py tests/test_scenario_replay_controls.py tests/test_scenario_e2e.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-TIM-001` (bounded observable collection lateness across recovery paths); the focused collector/recovery/source-health/Android suite passed 11 tests. This is development fixture evidence and does not claim target timing qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/3a7d2cf5ae4f633c9cd93ab15e67227ae631b4c8e146dad2822c4467e040a671.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collector.py tests/test_recovery.py tests/test_source_health_lifecycle.py tests/test_android_sensor_bridge.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-TIM-002` (late-context handling without incident identity/history rewriting); the focused incident/context suite passed 18 tests. This is development fixture evidence and does not claim target timing qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/23087b375b936f1922d45fb1dc423a1116e092ddb820ee10f25f6619bcea8919.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_incidents.py tests/test_incident_identity.py tests/test_incident_commands_and_relations.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-DET-001` (byte-exact, tolerance-bound and semantic replay-check classification); the focused replay/benchmark/review suite passed 7 tests. This is development fixture evidence and does not claim target benchmark qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/56771a73ecd640a02348343cdb6bdd1ae48e217b6feb75db0f86cbc51a8c343f.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_replay_verification.py tests/test_scenario_e2e.py tests/test_benchmark_lab.py tests/test_after_event_review.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added receipt-backed implementation evidence for `REQ-DET-002` (deterministic near-threshold abstention across hazards); the focused threshold/hazard/flood-landslide suite passed 24 tests. This is development fixture evidence and does not claim target model-quality qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/fa5ad77e27db42b2ddcdb305d450267a2f68d23a4b8cd6d452d006df1ef4ae43.json`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_threshold_abstention.py tests/test_hazards.py tests/test_flood_landslide_contracts.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Added a receipt-backed collaborative transport slice: deterministic MIME encoding/decoding for the fixed Sentinel Collaborative Signal v1 subject, bounded JSON/email sizes, exactly-one signal-part enforcement, and inbound rejection for duplicates, expiry and replay. The focused collaboration suite passed 13 tests. This is experimental email-wire/fixture evidence; it does not claim Gmail or physical-peer qualification.
- Changed paths: `src/sentinel_edge/collaboration/wire.py`, `src/sentinel_edge/collaboration/__init__.py`, `tests/test_collaboration_wire.py`, `provenance/evidence/aabc8e7a73a10bea1dcd9344081c1ba196814e93e4a61a289b1fd676fd3e6dd7.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_wire.py tests/test_collaboration_contracts.py tests/test_collaboration_policy.py`.
- Added a receipt-backed experimental SMTP outbound slice: credential-free sender port, bounded queue, expiry/age limits, unchanged-update suppression, deterministic bounded exponential retry with jitter, and dead-letter behavior. The focused collaboration suite passed 16 tests; no external SMTP or Gmail qualification is claimed.
- Changed paths: `src/sentinel_edge/collaboration/smtp.py`, `src/sentinel_edge/collaboration/__init__.py`, `tests/test_collaboration_smtp.py`, `provenance/evidence/87eedab4ee5565d58021507ad96522d61eaab493ec02e5999ae180fc045c15bc.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_smtp.py tests/test_collaboration_wire.py tests/test_collaboration_contracts.py tests/test_collaboration_policy.py`.
- Added a receipt-backed experimental Gmail polling connector: narrow client port, bounded recent-message query, durable message-id idempotency, MIME/schema/policy rejection, Component-1 envelope emission with `email_unverified` trust, and processed/rejected label mutation after local handling. The fake-Gmail collaboration suite passed 18 tests; no Gmail credentials or live mailbox qualification is claimed.
- Changed paths: `src/sentinel_edge/collaboration/gmail.py`, `src/sentinel_edge/collaboration/__init__.py`, `tests/test_collaboration_gmail.py`, `provenance/evidence/7c0243cd4eeb130a9b3bf3b4e36096ae202a4a4710745c90c5bf92ba9f789fd8.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_gmail.py tests/test_collaboration_smtp.py tests/test_collaboration_wire.py tests/test_collaboration_contracts.py tests/test_collaboration_policy.py`.
- Added a receipt-backed experimental collaboration REST boundary under `/v1/collaboration`: opt-in status, consent read/write with independent sharing/research validation, privacy-minimized signal listing, and explicit non-trusted correlation response. The API/collaboration suite passed 12 tests; endpoints use existing authentication and permission boundaries.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_collaboration_api.py`, `provenance/evidence/f1ada4f69fdb2a9e2ad2149ee94e6ae156b6b68e1fef4c722184cb37c6a6c96f.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_api.py tests/test_api.py tests/test_collaboration_gmail.py tests/test_collaboration_smtp.py tests/test_collaboration_wire.py`.
- Added a receipt-backed collaboration UI slice to the existing Web Client: authenticated status loading, explicit opt-in/research controls, experimental/email-unverified disclaimer, and in-memory-session behavior aligned with the existing client security model. The focused UI/API suite passed 7 tests.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `provenance/evidence/d1585542552f6250c507b9dc1f33e155c143e52ec0fd8245e10724f7b7351979.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_client_accessibility.py tests/test_client_security.py tests/test_web_boundary_integration.py tests/test_collaboration_api.py`.
- Tightened the collaboration UI/API slice so consent can be explicitly saved through the governed REST endpoint. The UI keeps the two consent decisions separate, reports permission/validation failures, and the API returns an auditable-save indicator. Focused API/client tests passed 6.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_collaboration_api.py`, `provenance/evidence/7a0f18adcc6cb305c1cc4dfc8f1ecebb128657b75f615414055e0b3b7143812f.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_api.py tests/test_client_accessibility.py tests/test_client_security.py`.
- Added append-only, privacy-minimized collaboration consent audit records to the authenticated gateway. Each consent change records actor, timestamp, previous/new consent booleans and policy version; status exposes count/latest audit without secrets or raw signals. Focused API/client tests passed 6.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_collaboration_api.py`, `provenance/evidence/0cd50ae9375121e5569b61b3ba9f53b7d92df3ce2f90aff4ed9d3c0fddfa028f.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_api.py tests/test_client_accessibility.py tests/test_client_security.py`.
- Expanded `config/collaboration.yaml` to the specification's explicit disabled-by-default profile: capability/mode, consent hazards, privacy prohibitions, bounded outbound queue, Gmail polling labels/query, correlation policy and retention controls. Added deterministic config safety coverage; collaboration/API/transport suite passed 12 tests.
- Changed paths: `config/collaboration.yaml`, `tests/test_collaboration_config.py`, `provenance/evidence/a4fd0ed045dfff18858cb1a1cc61e505ded1ec0500901567ae7acf1415b8f92e.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_config.py tests/test_collaboration_api.py tests/test_collaboration_gmail.py tests/test_collaboration_smtp.py tests/test_collaboration_wire.py`.
- Added fail-closed collaboration configuration validation for supported modes, disabled/fixture transport boundaries, separate research consent, email credential references, and forbidden raw/exact privacy settings. The collaboration/config/API/transport suite passed 15 tests.
- Changed paths: `src/sentinel_edge/collaboration/config.py`, `src/sentinel_edge/collaboration/__init__.py`, `tests/test_collaboration_config_validation.py`, `provenance/evidence/c81a3534168a91c7e9a17c52ab87b4455976900c646f1278cfa2abe67d521908.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_config_validation.py tests/test_collaboration_config.py tests/test_collaboration_api.py tests/test_collaboration_gmail.py tests/test_collaboration_smtp.py tests/test_collaboration_wire.py`.
- Replaced the empty collaboration correlation read projection with deterministic correlation evaluation over normalized stored signals, preserving `email_unverified` review-only semantics; added the incident collaboration projection shape with policy, peer/trust counts, summaries and explicit no-trusted-confirmation state. API/incident regression suite passed 7 tests.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_collaboration_api.py`, `provenance/evidence/0d0c38d42884e00319a04cbaef86b38ee53b52d8efa56e5fec69fd9a38b40469.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_api.py tests/test_api.py tests/test_incident_identity_api.py`.
- Added an explicit privacy transformation boundary for collaboration: stable pseudonymous node IDs derived from a local secret and opaque coarse correlation-domain IDs derived before signal construction. Invalid/missing identity, coordinates and precision fail closed; the collaboration suite passed 24 tests.
- Changed paths: `src/sentinel_edge/collaboration/privacy.py`, `src/sentinel_edge/collaboration/__init__.py`, `tests/test_collaboration_privacy.py`, `provenance/evidence/17cc9759f891a6d84a3521730df91c5b3f94446a41ff83bcc0170e358abff991.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_privacy.py tests/test_collaboration_config_validation.py tests/test_collaboration_api.py tests/test_collaboration_gmail.py tests/test_collaboration_smtp.py tests/test_collaboration_wire.py tests/test_collaboration_policy.py`.
- Added an explicit offline `FixtureCollaborativeSignalPublisher` for the local opt-in phase. It emits only schema-validated derived signals when consent/materiality permits, labels simulated source mode, and never sends network data or mutates incidents. Focused collaboration suite passed 16 tests.
- Changed paths: `src/sentinel_edge/collaboration/fixture.py`, `src/sentinel_edge/collaboration/__init__.py`, `tests/test_collaboration_fixture.py`, `provenance/evidence/834cce3cdb1bdd1a42ec7e6f2f0fa2e0250c907f877704d47923e3aeeadd2157.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_fixture.py tests/test_collaboration_privacy.py tests/test_collaboration_config_validation.py tests/test_collaboration_policy.py tests/test_collaboration_wire.py`.
- Ran the specification's documented offline `scripts/dev.py collaboration-demo` successfully: two independent simulated peers produce `MULTI_NODE_TRIGGER_SIMULATED` with fixture-qualified trust. The combined collaboration Definition-of-Done suite passed 29 tests, covering disabled/default-off safety, privacy/config validation, fixture/transport behavior, Gmail fake polling, API/UI boundaries and security.
- Changed paths/evidence: `config/collaboration.yaml`, `architecture/collaboration-policy.yaml`, `src/sentinel_edge/collaboration/fixture.py`, `src/sentinel_edge/gateway/api.py`, `provenance/evidence/d08b02ca41596a4454d889362384fbba3294b63e7931b7b0095be5ee3ffe3093.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/dev.py collaboration-demo`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_config.py tests/test_collaboration_config_validation.py tests/test_collaboration_fixture.py tests/test_collaboration_privacy.py tests/test_collaboration_policy.py tests/test_collaboration_wire.py tests/test_collaboration_smtp.py tests/test_collaboration_gmail.py tests/test_collaboration_api.py tests/test_client_accessibility.py tests/test_client_security.py`.
- Extended the collaboration signal REST projection with bounded `hazard`, `validation_state`, `transport`, `limit<=200` and cursor filters. Responses now expose only safe signal summaries plus pagination metadata; raw MIME, OAuth material and other secrets remain excluded. API regression suite passed 7 tests.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_collaboration_api.py`, `provenance/evidence/be32c285a7488f469e6e82792a1944b0a6219943ca9e33177c79cb096976d977.json`, `HACKATHON_WORKLOG.md`.
- Exact verification command: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_api.py tests/test_api.py`.
- Post-change regression verification passed: requirement closure, conformance ledger, evidence registry and all 12 G0 gate statuses are valid; the focused collaboration/UI suite passed 22 tests. The aggregate `scripts/dev.py gates` command was also attempted with its documented 300-second bound but timed out without a result, so it is not treated as passing evidence.
- Changed paths/evidence: `qualification/conformance-ledger.json`, `qualification/g0-gate-status.json`, `provenance/evidence/a58bd75a0ace46a54ac37699fe41702167fb1da544396e16de5d9b70052927c1.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe scripts/dev.py gates` (timeout after 300 seconds); `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/validate_evidence_registry.py`; `.venv\\Scripts\\python.exe scripts/validate_g0_gate_status.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_api.py tests/test_collaboration_config_validation.py tests/test_collaboration_fixture.py tests/test_collaboration_privacy.py tests/test_collaboration_gmail.py tests/test_collaboration_smtp.py tests/test_collaboration_wire.py tests/test_client_accessibility.py tests/test_client_security.py`.
- Formalized receipt-backed H1 implementation for `REQ-HIS-001` and `REQ-HIS-002`: event/knowledge ordering and late-context history preservation, plus explicit claim supersession without rewriting prior state. Added registry test mapping and regenerated conformance/scope/release projections. Focused history and projection tests passed.
- Changed paths: `tests/test_history_requirements.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/ec631ff41d8662c3f7895d9d11c6848e50176700a95670f42443579a00489bcc.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_history_requirements.py tests/test_incidents.py tests/test_claim_lineage.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Formalized receipt-backed H1 implementation for `REQ-HIS-003`: governed privacy deletion removes private artifact bytes, preserves lawful historical linkage/tombstone state, invalidates active claim support, and does not mutate incident history. Added registry mapping and regenerated projections; focused lifecycle and conformance tests passed.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/bf196626db65fa6dddb09653c71d06d33f611b3037dd1ab6ca5e3f9942ed600b.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_evidence_lifecycle.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Added explicit `principal_kind` classification (`human|service|device|system`) to `PrincipalRef`; authorization decisions now preserve this alongside subject, authentication method and policy version. Formalized receipt-backed implementation for `REQ-PRN-001`, regenerated projections, and passed the focused identity/auth/security and conformance suites.
- Changed paths: `src/sentinel_edge/domain/models.py`, `tests/test_principal_kind_trace.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/619cb3f9c015a5b4bf83f7230e0c3dfeefc3dc1e44c50bb1bc2bed44d71f468a.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_principal_kind_trace.py tests/test_auth_and_commands.py tests/test_client_security.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Added fail-closed review authority for non-human principals: service/device/system principals are denied `reviews:generate` even if a role is overbroad; human operators retain the permission. Formalized receipt-backed `REQ-PRN-002`, regenerated projections, and passed identity/auth/conformance suites.
- Changed paths: `src/sentinel_edge/security/auth.py`, `tests/test_principal_review_authority.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/3e6ec60b5014dc32c4b8f22253c5aff6486507ee7890a482654a25401be35135.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_principal_review_authority.py tests/test_principal_kind_trace.py tests/test_auth_and_commands.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Formalized receipt-backed `REQ-WEB-005`: the web security policy rejects non-loopback plaintext bearer transport, requires HTTPS for non-loopback service mode, and keeps loopback plaintext explicitly opt-in. Regenerated projections and passed web/security/conformance suites.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/e21e259f6d76b86bfb970097787a5727450f57717fba31d19ef7f43bd09e825c.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_web_security_policy.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Enforced the browser-write security boundary in the gateway for `REQ-WEB-004`: unsafe `/v1` requests carrying an `Origin` now require an allowed origin and non-empty CSRF token; bearer-only non-browser API clients remain compatible. Formalized the receipt-backed requirement, regenerated projections, and passed web/security/conformance suites.
- Changed paths: `src/sentinel_edge/gateway/api.py`, `tests/test_web_security_policy.py`, `tests/test_web_boundary_integration.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/65bff476604017bde0bc0301d84b046b8b6cb59faa62c571112b73adbb19c8b0.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_web_security_policy.py tests/test_web_boundary_integration.py tests/test_client_security.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Added an explicit fail-closed WebSocket upgrade policy for `REQ-WEB-003`: projection upgrades require both an allowed Origin and authenticated principal, with no mutation semantics. Formalized the receipt-backed requirement, regenerated projections, and passed web/security/conformance suites.
- Changed paths: `src/sentinel_edge/gateway/web_security.py`, `tests/test_web_security_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/cf19d208c32b5ccfc02014710d54526b02c46e23941442f8a2299b2e60820a34.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_web_security_policy.py tests/test_web_boundary_integration.py tests/test_client_security.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Formalized receipt-backed `REQ-LIV-004`: live projection stream cursors remain separate from incident versions, idempotency keys and audit identity, with reconnect/resync behavior covered by the projection suite. Regenerated projections and passed conformance checks.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/5c4d0c7fb162fff2e950ddabc5357b627d7617de71b5e183a73847b45582c138.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Implemented bounded per-client live projection buffering for `REQ-LIV-003`: a slow client cannot grow memory without bound; overflow deterministically clears delivery state and requires REST resynchronization. Recorded immutable receipt and regenerated all qualification projections.
- Changed paths: `src/sentinel_edge/projections/service.py`, `tests/test_projection_client_buffer.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/df1a1f29edb7365b12465acb748070ceb58a9cca4c4f0e509f7fc03cb18aedd8.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_projection_client_buffer.py tests/test_live_projections_and_offline.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_projection_client_buffer.py tests/test_live_projections_and_offline.py" --revision working-tree --result passed --duration-seconds 12 --environment emulated-aarch64-dev --input src/sentinel_edge/projections/service.py --input tests/test_projection_client_buffer.py --input tests/test_live_projections_and_offline.py --passed 7`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`; `.venv\\Scripts\\python.exe -m pytest -q tests/test_conformance_ledger.py tests/test_scope_freeze.py tests/test_release_minimum_manifest.py tests/test_g0_gate_status.py`.
- Implemented `REQ-CNX-003` polling contract: Gmail collaboration polling now has deterministic message ordering, a bounded `max_inflight`, explicit heartbeat timestamp, and a durable message cursor; overflow is reported without unbounded work. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/collaboration/gmail.py`, `tests/test_collaboration_gmail.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/2428e13bb852bfca66e24d18cfb654add22364b9a910abd163f9d7663dd47492.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_gmail.py tests/test_collaboration_config.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_collaboration_gmail.py tests/test_collaboration_config.py" --revision working-tree --result passed --duration-seconds 3 --environment emulated-aarch64-dev --input src/sentinel_edge/collaboration/gmail.py --input tests/test_collaboration_gmail.py --input tests/test_collaboration_config.py --input config/collaboration.yaml --passed 4`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Formalized `REQ-CMP-012`: offline mobile command preparation/reconciliation is minimal and reauthorized, replay is idempotent, and payload, principal, stale-base and expiry conflicts remain visible as explicit failures. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/adfee7abb57da5f774598ad05ffb7f396e00bca95e56701718a3c4bc7277355e.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py tests/test_auth_and_commands.py tests/test_incident_commands_and_relations.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py tests/test_auth_and_commands.py tests/test_incident_commands_and_relations.py" --revision working-tree --result passed --duration-seconds 14 --environment emulated-aarch64-dev --input src/sentinel_edge/gateway/api.py --input src/sentinel_edge/incidents/engine.py --input tests/test_live_projections_and_offline.py --input tests/test_auth_and_commands.py --input tests/test_incident_commands_and_relations.py --passed 18`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-ACT-002` closure guard: qualification state remains open when neither evidence nor an explicit accepted-debt identifier is supplied, and closes only with one of those declared bases. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/qualification/assurance_case.py`, `tests/test_assurance_closure.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/39f48f67ed3b17b6718884d8df30d1f1205225a78a865e030cb0a75374fc1875.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_assurance_closure.py tests/test_assurance_case.py tests/test_qualification_lifecycle_v021.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_assurance_closure.py tests/test_assurance_case.py tests/test_qualification_lifecycle_v021.py" --revision working-tree --result passed --duration-seconds 9 --environment emulated-aarch64-dev --input src/sentinel_edge/qualification/assurance_case.py --input tests/test_assurance_closure.py --input tests/test_assurance_case.py --input tests/test_qualification_lifecycle_v021.py --passed 8`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-LOC-002`: collaboration privacy now exposes an explicit trust decision proving that exact or coarse location cannot verify a source; only independent source verification can do so. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/collaboration/privacy.py`, `tests/test_location_trust.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/317ddf0451e76858c7478d2ad21455258c8e206f513b828fe1d853e326818f8c.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_location_trust.py tests/test_collaboration_policy.py tests/test_collaboration_config.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_location_trust.py tests/test_collaboration_policy.py tests/test_collaboration_config.py" --revision working-tree --result passed --duration-seconds 2 --environment emulated-aarch64-dev --input src/sentinel_edge/collaboration/privacy.py --input tests/test_location_trust.py --input tests/test_collaboration_policy.py --input tests/test_collaboration_config.py --passed 10`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-ARL-003`: restricted artifact reads now explicitly separate authorization from digest disclosure; unauthorized responses omit protected digests while authorized verification reads may disclose them. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/59e3e541689a4dcddbed11f6797b507a3023ab2b9b7e719c0b8e58b8cf325ab2.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_artifact_read_authorization.py tests/test_artifact_governance.py tests/test_privacy_export_api.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_artifact_read_authorization.py tests/test_artifact_governance.py tests/test_privacy_export_api.py" --revision working-tree --result passed --duration-seconds 6 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/artifact_governance.py --input tests/test_artifact_read_authorization.py --input tests/test_artifact_governance.py --input tests/test_privacy_export_api.py --passed 8`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-ARL-004`: active incident artifact references now demonstrably block deletion while the artifact remains verifiable. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `tests/test_artifact_reference_contract.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/596eef935f38faa48ef8460d1334cb1ff747173e59ce67c220bcde273096654f.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_artifact_reference_contract.py tests/test_artifact_read_authorization.py tests/test_artifact_governance.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_artifact_reference_contract.py tests/test_artifact_read_authorization.py tests/test_artifact_governance.py" --revision working-tree --result passed --duration-seconds 4 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/artifacts.py --input src/sentinel_edge/storage/artifact_governance.py --input tests/test_artifact_reference_contract.py --input tests/test_artifact_read_authorization.py --input tests/test_artifact_governance.py --passed 12`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-ARL-005`: restore verification applies governed tombstones before readiness, validates archive/reference closure, and rejects invalid closure states. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/098fb7745b65c0ce353f0d267a83b75b5fe4b84ba0f0e71b562627e34ad7f256.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py tests/test_authority_watermark_closure.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py tests/test_authority_watermark_closure.py" --revision working-tree --result passed --duration-seconds 29 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/backup.py --input src/sentinel_edge/privacy/closure.py --input tests/test_privacy_backup_and_exports.py --input tests/test_storage_backup_and_spool.py --input tests/test_authority_watermark_closure.py --passed 20`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Formalized `REQ-CAU-004`: durable command/inbox receipts survive backup/restart, and duplicate replay returns the original committed effect rather than applying a second mutation. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/cdd663ca0e90cf25f82e187df2ab0aa72fc089b1e8339dc950b942ef1244fef4.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py tests/test_auth_and_commands.py tests/test_api_workflows.py tests/test_incident_commands_and_relations.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py tests/test_auth_and_commands.py tests/test_api_workflows.py tests/test_incident_commands_and_relations.py" --revision working-tree --result passed --duration-seconds 14 --environment emulated-aarch64-dev --input src/sentinel_edge/incidents/engine.py --input src/sentinel_edge/storage/sqlite_store.py --input tests/test_live_projections_and_offline.py --input tests/test_auth_and_commands.py --input tests/test_api_workflows.py --input tests/test_incident_commands_and_relations.py --passed 19`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Formalized `REQ-CLC-004`: offline pending commands are minimal, bounded command data with references only; raw evidence and secrets are excluded, and tickets expire/reconcile under policy. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/983428c97f038a6803f6b28325d8c30ded7d96fbf043bf32177ae9890cf4be14.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_live_projections_and_offline.py" --revision working-tree --result passed --duration-seconds 8 --environment emulated-aarch64-dev --input src/sentinel_edge/gateway/offline.py --input src/sentinel_edge/incidents/engine.py --input tests/test_live_projections_and_offline.py --passed 5`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-AUP-004`: non-human machine/system principals are bound to the authenticated sending component; mismatches are denied with an explicit audited reason, while human principals remain role-governed. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/security/auth.py`, `tests/test_producer_identity.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/ce4855cb576c3453d3a6d664714e26afdb2a02335dd52dbb9115c4a160b2bf64.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_producer_identity.py tests/test_principal_kind_trace.py tests/test_principal_review_authority.py tests/test_auth_and_commands.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_producer_identity.py tests/test_principal_kind_trace.py tests/test_principal_review_authority.py tests/test_auth_and_commands.py" --revision working-tree --result passed --duration-seconds 7 --environment emulated-aarch64-dev --input src/sentinel_edge/security/auth.py --input tests/test_producer_identity.py --input tests/test_principal_kind_trace.py --input tests/test_principal_review_authority.py --input tests/test_auth_and_commands.py --passed 10`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-SUP-003`: CycloneDX 1.7 inventory now includes declared components, SHA-256 hashes for resolved distributions, license metadata and explicit dependency relationships, with scope limitations retained. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/release/sbom.py`, `tests/test_supply_chain_evidence.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/8af24a4efb11cf122e43f259f28240b1d6b99cfccbd903a480212f51f18c2952.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_supply_chain_evidence.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_supply_chain_evidence.py" --revision working-tree --result passed --duration-seconds 6 --environment emulated-aarch64-dev --input src/sentinel_edge/release/sbom.py --input tests/test_supply_chain_evidence.py --passed 4`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-AIT-001`: generated and analytically modeled claims now require an explicit model identifier and non-empty lineage, while source/operator content remains separately classified. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/domain/models.py`, `tests/test_content_origin.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/e9ee93d1a8dd7fd0ede6a8224ab96c6d00e04983f24d0d2000a2ec5fc2aeba8a.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_content_origin.py tests/test_evidence_claim_graph.py tests/test_evidence_api.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_content_origin.py tests/test_evidence_claim_graph.py tests/test_evidence_api.py" --revision working-tree --result passed --duration-seconds 4 --environment emulated-aarch64-dev --input src/sentinel_edge/domain/models.py --input tests/test_content_origin.py --input tests/test_evidence_claim_graph.py --input tests/test_evidence_api.py --passed 10`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-WHK-001` and `REQ-WHK-002`: raw webhook bytes are HMAC-authenticated with bounded timestamp/skew and size checks before semantic processing; provider delivery identity is claimed once for replay-safe idempotency. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/qualification/webhook_security.py`, `tests/test_webhook_security.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/affedf7f1f87b8b2ad101f31e75a321e43e2b3bf6768a7a80e0f5b74e241ed8f.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_webhook_security.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_webhook_security.py" --revision working-tree --result passed --duration-seconds 2 --environment emulated-aarch64-dev --input src/sentinel_edge/qualification/webhook_security.py --input tests/test_webhook_security.py --passed 2`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-TVA-001` and `REQ-TVA-002`: added a machine-readable timer policy covering artifact grants, source TTL, offline commands, sessions, outbox expiry and artifact retention, plus monotonic same-boot authority checks that fail closed across reboot, rollback or expiry. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/runtime/timer_policy.py`, `tests/test_timer_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/3e7a35e0059cc5c556ef5c04b508d62b569156bb4741a8a06bc1cdb433350cec.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_timer_policy.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_timer_policy.py" --revision working-tree --result passed --duration-seconds 1 --environment emulated-aarch64-dev --input src/sentinel_edge/runtime/timer_policy.py --input tests/test_timer_policy.py --passed 3`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-EVO-002`: schema evolution migrates or quarantines N-1 artifacts with precise incompatibility reasons and blocks mixed incompatible workers during handshake. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/evolution/contracts.py`, `src/sentinel_edge/evolution/wire.py`, `tests/test_schema_evolution.py`, `tests/contracts/test_compatibility.py`, `tests/contracts/test_round_trip_contracts.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/8ee7326364d01ecf3841e1e5f39852a780a34bfcd2c723ecdb61b3127df1f342.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_schema_evolution.py tests/contracts/test_compatibility.py tests/contracts/test_round_trip_contracts.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_schema_evolution.py tests/contracts/test_compatibility.py tests/contracts/test_round_trip_contracts.py" --revision working-tree --result passed --duration-seconds 4 --environment emulated-aarch64-dev --input src/sentinel_edge/evolution/contracts.py --input src/sentinel_edge/evolution/wire.py --input tests/test_schema_evolution.py --input tests/contracts/test_compatibility.py --input tests/contracts/test_round_trip_contracts.py --passed 9`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-TVA-003`, `REQ-TVA-004` and `REQ-TVA-005`: cross-reboot high-impact actions require trusted UTC and reconfirmation when stale; retention GC cannot fire from an untrusted forward wall-clock step; ambiguous source age becomes non-influential. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/runtime/timer_policy.py`, `tests/test_timer_policy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/f8b68d7940d8e72bfb138759e8a00e48b269c744a6373ec55a36744012b358e1.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_timer_policy.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_timer_policy.py" --revision working-tree --result passed --duration-seconds 1 --environment emulated-aarch64-dev --input src/sentinel_edge/runtime/timer_policy.py --input tests/test_timer_policy.py --passed 6`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-DLR-001`, `REQ-DLR-002`, `REQ-DLR-003`, `REQ-DLR-004` and `REQ-DLR-006`: added bounded immutable dead-letter records with envelope/payload hash, aggregate isolation metadata, attempt limits, preserved causation/correlation/idempotency lineage, mandatory redrive revalidation, and capacity bounds. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/runtime/dead_letter.py`, `tests/test_dead_letter.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/9c3410d614caef357b99c7fbc6f699ab1c48c84f8cf34574ae518eb0d55cd8ed.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_dead_letter.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_dead_letter.py" --revision working-tree --result passed --duration-seconds 1 --environment emulated-aarch64-dev --input src/sentinel_edge/runtime/dead_letter.py --input tests/test_dead_letter.py --passed 2`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-BDR-002`, `REQ-BDR-006` and `REQ-BDR-007`: ordinary backups persist secret metadata only, restore reapplies the current deletion/tombstone floor before exposure, and module checkpoints use SQLite online backup rather than unsafe main-file copying. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/storage/backup.py`, `src/sentinel_edge/privacy/closure.py`, `src/sentinel_edge/privacy/tombstones.py`, `tests/test_privacy_backup_and_exports.py`, `tests/test_storage_backup_and_spool.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/f3d0f6ce6ab45c4d2820f38ed8aa840569d8887081900c82fcea2d6d03df9a40.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py" --revision working-tree --result passed --duration-seconds 24 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/backup.py --input src/sentinel_edge/privacy/closure.py --input src/sentinel_edge/privacy/tombstones.py --input tests/test_privacy_backup_and_exports.py --input tests/test_storage_backup_and_spool.py --passed 16`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-BPR-004`: restore extracts into an isolated staging namespace, verifies integrity and disposition, applies tombstones, validates schema/reference/authority convergence, and only atomically exposes the target after readiness checks. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/storage/backup.py`, `tests/test_privacy_backup_and_exports.py`, `tests/test_storage_backup_and_spool.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/f3d0f6ce6ab45c4d2820f38ed8aa840569d8887081900c82fcea2d6d03df9a40.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-BPR-001`: added an AES-GCM authenticated encrypted backup envelope whose recovery key is supplied by a separate authority and never stored in the backup payload; wrong-key and missing-reference paths fail closed. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/storage/encrypted_backup.py`, `tests/test_encrypted_backup.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/74f95e581f4838afb60f42a38f7cf789cacf3ee0c2b08b39c475196a0c6cb58d.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_encrypted_backup.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_encrypted_backup.py" --revision working-tree --result passed --duration-seconds 7 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/encrypted_backup.py --input tests/test_encrypted_backup.py --passed 2`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-CLC-006`: added a lock-screen notification projection that suppresses exact hazard details, location, sender and media text for sensitive incidents while retaining a safe actionable prompt. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/security/notification_privacy.py`, `tests/test_notification_privacy.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/ebe6f38f064f00f8efaff6f4844878f69cffaa76f4144f630498836ca94332eb.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_notification_privacy.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_notification_privacy.py" --revision working-tree --result passed --duration-seconds 1 --environment emulated-aarch64-dev --input src/sentinel_edge/security/notification_privacy.py --input tests/test_notification_privacy.py --passed 2`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-CLC-003`: restricted offline evidence now requires the declared protected-native-client profile, native-client identity, authentication and protected storage; unprotected/web callers fail closed. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/gateway/protected_client.py`, `tests/test_protected_client.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/7e5f49b1d4005aec45cbd7b1924588beca1eafaa9433a0eb444799e21fa89f56.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_protected_client.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_protected_client.py" --revision working-tree --result passed --duration-seconds 1 --environment emulated-aarch64-dev --input src/sentinel_edge/gateway/protected_client.py --input tests/test_protected_client.py --passed 1`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-BPR-003`: restore now requires explicit actor, reason, target node/namespace and policy version authorization, validates target binding before extraction, and the CLI requires the same fields. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/storage/restore_authorization.py`, `src/sentinel_edge/storage/backup.py`, `src/sentinel_edge/cli.py`, `tests/test_privacy_backup_and_exports.py`, `tests/test_storage_backup_and_spool.py`, `tests/test_authority_watermark_closure.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/cf35b4fbc44e8b8dedfd2e9f08e632a90df7c18f8147617602fc871b7f6eeabf.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py tests/test_authority_watermark_closure.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_privacy_backup_and_exports.py tests/test_storage_backup_and_spool.py tests/test_authority_watermark_closure.py" --revision working-tree --result passed --duration-seconds 40 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/backup.py --input src/sentinel_edge/storage/restore_authorization.py --input tests/test_privacy_backup_and_exports.py --input tests/test_storage_backup_and_spool.py --input tests/test_authority_watermark_closure.py --passed 20`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-BPR-005`: restored state explicitly records that live credentials are not rebound and recovery is mandatory before authentication; backup restore never revives old deployment credentials. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/storage/backup.py`, `tests/test_storage_backup_and_spool.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/0e8bb3403eeffe5adc0f2e7a4e653446f1e3d13b5087b47680350da8cc36dca4.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_storage_backup_and_spool.py tests/test_privacy_backup_and_exports.py tests/test_authority_watermark_closure.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_storage_backup_and_spool.py tests/test_privacy_backup_and_exports.py tests/test_authority_watermark_closure.py" --revision working-tree --result passed --duration-seconds 48 --environment emulated-aarch64-dev --input src/sentinel_edge/storage/backup.py --input tests/test_storage_backup_and_spool.py --input tests/test_privacy_backup_and_exports.py --input tests/test_authority_watermark_closure.py --passed 20`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-SRL-006` and `REQ-SRL-007`: source transport, completeness, freshness and decision influence remain independent; source fingerprint transitions invalidate prior qualification and require requalification. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/integrations/source_quality.py`, `src/sentinel_edge/qualification/sources.py`, `tests/test_source_quality.py`, `tests/test_camera_model_source_qualification.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/0447aece00784a0600763e8205b1cc8f1274fd866f10c5c2345bcb815b957938.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_source_quality.py tests/test_camera_model_source_qualification.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_source_quality.py tests/test_camera_model_source_qualification.py" --revision working-tree --result passed --duration-seconds 8 --environment emulated-aarch64-dev --input src/sentinel_edge/integrations/source_quality.py --input src/sentinel_edge/qualification/sources.py --input tests/test_source_quality.py --input tests/test_camera_model_source_qualification.py --passed 11`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-SAI-002`: advisory review matches exact component identity/version and preserves platform, feature-predicate and VEX subject evidence; broad product-name matching cannot clear unrelated artifacts. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/release/advisories.py`, `tests/test_provenance_and_advisories.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/2d585c532f9e19075d23655aa72cac53ed573eda62fa5c1ece6d8b94861f6840.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_provenance_and_advisories.py -k advisory`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_provenance_and_advisories.py -k advisory" --revision working-tree --result passed --duration-seconds 2 --environment emulated-aarch64-dev --input src/sentinel_edge/release/advisories.py --input tests/test_provenance_and_advisories.py --passed 1`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
- Implemented `REQ-SRL-003`: release lint now rejects non-HTTPS, credential-bearing, fragment-bearing or malformed critical source links and marks historical references explicitly non-current without network inference. Recorded immutable receipt and regenerated qualification projections.
- Changed paths: `src/sentinel_edge/qualification/sources.py`, `tests/test_source_link_validation.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `qualification/conformance-ledger.json`, `qualification/scope-freeze.json`, `qualification/release-minimum-manifest.json`, `qualification/g0-gate-status.json`, `qualification/deferred-debt-register.json`, `qualification/residual-risk-register.json`, `provenance/evidence/3b3ef0501256e9cc6a3917f0fb62321d938409de7d464150987af226b5d3e606.json`, `HACKATHON_WORKLOG.md`.
- Exact verification commands: `.venv\\Scripts\\python.exe -m pytest -q tests/test_source_link_validation.py`; `.venv\\Scripts\\python.exe scripts/record_test_evidence.py --command ".venv\\Scripts\\python.exe -m pytest -q tests/test_source_link_validation.py" --revision working-tree --result passed --duration-seconds 1 --environment emulated-aarch64-dev --input src/sentinel_edge/qualification/sources.py --input tests/test_source_link_validation.py --passed 2`; `.venv\\Scripts\\python.exe scripts/generate_conformance_ledger.py`; `.venv\\Scripts\\python.exe scripts/generate_scope_freeze.py`; `.venv\\Scripts\\python.exe scripts/generate_release_minimum_manifest.py`; `.venv\\Scripts\\python.exe scripts/generate_g0_gate_status.py`; `.venv\\Scripts\\python.exe scripts/generate_deferred_risk_registers.py`; `.venv\\Scripts\\python.exe scripts/validate_requirement_closure.py`; `.venv\\Scripts\\python.exe scripts/validate_conformance_ledger.py`.
## 2026-08-13 — Revision slice: evidence retraction supersession

- Implemented `REQ-REV-005`: evidence lifecycle retraction invalidates current claim support and records an immutable reevaluation while preserving the historical claim link and lifecycle trace.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/6a54c8ec857f998705874e1979b5ad7e204dbcda07bbe7824b6fea02096f7d4d.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_evidence_lifecycle.py` (3 passed).
## 2026-08-13 — Webhook key rotation

- Implemented `REQ-WHK-004`: webhook verification supports one bounded grace key and rejects the old key after the declared overlap window.
- Changed paths: `src/sentinel_edge/qualification/webhook_security.py`, `tests/test_webhook_security.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/3196d48bb1d5572283bcf82c95fda47f333ad71b608421249e2c774f2f5408ce.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_webhook_security.py` (3 passed).
## 2026-08-13 — Interrupted upload quarantine

- Implemented `REQ-UPL-006`: incomplete temporary artifact state is quarantined on recovery and remains outside ordinary artifact persistence.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/598e3591da89bb4e029c725bc684a442ad2c938bea284d6ff5baaa318ad68f1b.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_artifacts_and_claims.py` (5 passed; existing warning recorded).
## 2026-08-13 — Webhook sender identity

- Implemented `REQ-WHK-005`: webhook acceptance requires cryptographic sender proof; network placement alone cannot authenticate a request.
- Changed paths: `tests/test_webhook_security.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/e47512e99e0b589777a4fdef9e9e3897d454b2d1ea7fe0ebe9de0d11db28ab10.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_webhook_security.py` (4 passed).
## 2026-08-13 — Release candidate reopening

- Implemented `REQ-RCI-004`: a change to bound security qualification evidence invalidates the prior candidate instead of inheriting its status.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/ba9ddd058ad8d7b10a5594548b8a17132e526292276514f8e0f615e23a9f9170.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_candidate.py -k candidate_reopens_when_bound_security_review_changes` (1 passed; existing warning recorded).
## 2026-08-13 — Late correction notification suppression

- Implemented `REQ-REV-003`: late event-time corrections amend durable history without moving the watermark or emitting a fresh current-onset notification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/ef6b78bab81c5e520bbe84f60fbda7129da109cacd9608e9275c358f71e8f5b6.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_incidents.py -k late_context tests/test_history_requirements.py -k late` (2 passed; existing warning recorded).
## 2026-08-13 — Material reevaluation notifications

- Implemented `REQ-REV-004`: notification budgets suppress correction storms while material confirmation remains visible and notification identity remains idempotent.
- Changed paths: `tests/test_notifications_and_reviews.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/4b9904f8df86b98e5cd7762e8ad71e99e426e1377ea1ae79eb93f3f886f65bd6.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_notifications_and_reviews.py -k "grouped or snooze or correction_storm"` (3 passed).
## 2026-08-13 — Candidate frozen/observed separation

- Implemented `REQ-RCI-005`: release-candidate identity records entrant-controlled artifacts separately from observed host and gate facts.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/44c42ddc1be542355088961487e1803724a1304d383bcba7170fdd9c3af809cc.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_candidate.py -k "identity_is_stable or separates_frozen"` (2 passed; existing warning recorded).
## 2026-08-13 — Offline clean-clone candidate verification

- Implemented `REQ-RCI-007`: candidate verification returns machine-readable output from a copied workspace while network access is explicitly forbidden.
- Changed paths: `tests/test_release_candidate.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/45832c954f2a2d42ddbf27e17408291ced9bc391b1db1199c9bac6c9c8279e7a.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_candidate.py -k network_independent` (1 passed; existing warning recorded).
## 2026-08-13 — Post-freeze exception closure

- Implemented `REQ-RCI-008`: scope-freeze exceptions now require an approver, reason, displaced work, affected requirements, and non-empty mandatory reruns; incomplete exceptions fail validation.
- Changed paths: `scripts/generate_scope_freeze.py`, `scripts/validate_scope_freeze.py`, `tests/test_scope_freeze.py`, `qualification/scope-freeze.json`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/c1fe65816268717c91cca0bcfd071946c95cd16d1d4804d3f00bbe74488f0c8c.json`.
- Exact verification commands: `.venv\Scripts\python.exe scripts/generate_scope_freeze.py`; `.venv\Scripts\python.exe -m pytest -q tests/test_scope_freeze.py` (3 passed).
## 2026-08-13 — Direct-upload grant lifecycle

- Implemented `REQ-UPL-003`: upload grants are scoped to a principal and purpose, single-use, expiring, and bound to the issuing boot.
- Changed paths: `src/sentinel_edge/qualification/upload_grants.py`, `tests/test_upload_grants.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/c684a8d3f1d69dcb62f039d1f0cd0ddf209e414bab39a1c43201188e66913edf.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_upload_grants.py` (3 passed).
## 2026-08-13 — Streaming upload quotas

- Implemented `REQ-UPL-004`: streaming upload sessions enforce byte, time, media-class, concurrency and storage limits while computing the SHA-256 digest of accepted bytes.
- Changed paths: `src/sentinel_edge/qualification/upload_limits.py`, `tests/test_upload_limits.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/81082695e4a096cc90385bc4cc416f65942ca53ef5f39c11d645ff9925b5fc91.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_upload_limits.py` (2 passed).
## 2026-08-13 — Untrusted upload media labels

- Formalized `REQ-UPL-005`: parser selection uses bounded signature detection, rejects declared MIME mismatches, and strips embedded metadata before producing a derivative.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/d2e0c51ee379b59e95101e940597b51935c9a764d3d7966b541f35c01bc3a99f.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_media_parser.py` (5 passed).
## 2026-08-13 — Direct-upload admission gate

- Implemented `REQ-UPL-001`: upload grants are issued only when authentication, authorization, quota, consent, and source-policy checks all pass.
- Changed paths: `src/sentinel_edge/qualification/upload_admission.py`, `tests/test_upload_admission.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/841d85c150b85e10df847f41f4ceecaa8e8350395c51bf35a933fed59de1ff2c.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_upload_admission.py` (1 passed).
## 2026-08-13 — Upload quarantine backpressure

- Implemented `REQ-UPL-002`: upload bytes stream into component-owned quarantine files with bounded chunk admission, atomic completion, and abort cleanup.
- Changed paths: `src/sentinel_edge/qualification/upload_quarantine.py`, `tests/test_upload_quarantine.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/6607cdcaf08d4bd743140708e3fc25b09ee58a7f5c5da83ce9ec191d49223307.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_upload_quarantine.py` (2 passed).
## 2026-08-13 — Upload normalized evidence envelope

- Implemented `REQ-UPL-007`: upload data must carry a valid digest and pass the normalized observation contract before it can enter analysis; upload completion alone has no incident side effect.
- Changed paths: `src/sentinel_edge/qualification/upload_envelope.py`, `tests/test_upload_envelope.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/7e954994def29a1ed82aa1551fc00f899700a004c655b34f87d6e74f821158f6.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_upload_envelope.py` (2 passed).
## 2026-08-13 — No person-level tracking from exposure context

- Implemented `REQ-IMP-004`: the evidence contract rejects person re-identification, preventing identity/device linkage from contextual media.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/d39cf85c6618b69f5fefd2565df0403fb49e36507b2d499ec5f990aa94cf0e78.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_evidence_claim_graph.py -k person_identification` (1 passed).
## 2026-08-13 — Exposure and hazard-confidence separation

- Implemented `REQ-IMP-002`: potential population/building exposure is carried as a separate estimate and can influence review priority without promoting hazard verification state.
- Changed paths: `src/sentinel_edge/qualification/exposure.py`, `tests/test_exposure_separation.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/483d6c456c37997da0ebf75a5b38253529ef3b9b093cd2431458087e8ba59870.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_exposure_separation.py` (1 passed).
## 2026-08-13 — Estimated exposure wording

- Implemented `REQ-IMP-003`: exposure output uses explicit estimated-potential-exposure wording and rejects affected, killed, or casualty phrasing.
- Changed paths: `src/sentinel_edge/qualification/exposure.py`, `tests/test_exposure_separation.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/25ec963d22366fca7ba3dae5e18361b3561cfe6b1b3f3cb6f6afcd210ef8d7cf.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_exposure_separation.py` (1 passed).
## 2026-08-13 — Versioned exposure review priority

- Implemented `REQ-IMP-005`: exposure review priority uses a versioned bounded rule with visible reason/duration and preserves the minimum monitoring cadence.
- Changed paths: `src/sentinel_edge/qualification/exposure.py`, `tests/test_exposure_separation.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/e9410efed621f6628cab1b6712c2a5713c8296b2ee0bebfeedfe1754ae96fa1e.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_exposure_separation.py` (2 passed).
## 2026-08-13 — Key compromise interval evidence

- Implemented `REQ-AKC-002` and `REQ-AKC-003`: compromise events preserve the known/unknown interval boundary and unknown compromise timing yields indeterminate historical verification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/a84e7e3b2e4ae146380c567dd78578696e3349aa009fc9cd79b7514f377a4a7f.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_audit_revocation_and_connector_lifecycle.py -k policy_revocation_preserves_prior_audit_semantics` (1 passed; existing warnings recorded).
## 2026-08-13 — Non-forensic audit wording

- Implemented `REQ-AKC-004`: local audit signatures retain explicit non-forensic wording and remain scoped to authentication/tamper evidence.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/aaa238124278721502e96373b6bd04b7122fa5a546eb3ec1e605ef1df71a89b1.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_audit_revocation_and_connector_lifecycle.py -k signed_audit_checkpoint_detects` (1 passed; existing warnings recorded).
## 2026-08-13 — Key rotation recovery

- Implemented `REQ-AKC-005`: new key generation rotation retires the prior generation, preserves historical verification, and rejects new heads signed by the old generation.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/40fcfb03e86246d6f591083bd4ad62234b0e4818cf024a2c1ac981000e9a7e28.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_audit_revocation_and_connector_lifecycle.py -k signed_audit_checkpoint_detects` (1 passed; existing warnings recorded).
## 2026-08-13 — Closed qualification vocabulary

- Implemented `REQ-CQL-001`: the generated qualification vocabulary is shared by lifecycle evaluations and rejects unknown states.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/9596550c1ab63bd7737e44126d034d863d8e43ce6c3ab53765703947f77c1cb6.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_qualification_lifecycle_v021.py` (4 passed).
## 2026-08-13 — Active current-contract snapshot

- Implemented `REQ-CQL-004`: the active-contract generator produces a compact current view from authoritative registries and contracts, with truthful release claims.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/f6e4678581254627bbb467ca57699149365d099bffed6a05c7d30cd24f975033.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_i01_active_contract_snapshot.py` (1 passed).
## 2026-08-13 — Active-contract candidate binding

- Implemented `REQ-CQL-005`: release-candidate identity now binds active-contract input digests and the generator version.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/3ddb1454976c7bcf4235aea221c2b77073c0ada74e49033674f4d02b72d12de4.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_candidate.py -k binds_active_contract` (1 passed; existing warning recorded).
## 2026-08-13 — Webhook acknowledgement bounds

- Implemented `REQ-WHK-003`: webhook verification now rejects deliveries exceeding the bounded acknowledgement window, alongside byte and cryptographic limits.
- Changed paths: `src/sentinel_edge/qualification/webhook_security.py`, `tests/test_webhook_security.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/1f1701177bdd3fa5fe5e9195db131f6878e63413837f50e65f8d39171a2bce15.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_webhook_security.py` (5 passed).
## 2026-08-13 — Release candidate dirty-state guard

- Implemented `REQ-RCI-003`: candidate identity records Git revision/dirty state, binds it during verification, and prevents dirty repositories from being admitted as releases.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/e41a32e6dddb0a1ec321c63a0169fc0b9879adce941843192ec9af8459c7c4c0.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_candidate.py -k repository_state` (1 passed; existing warning recorded).
## 2026-08-13 — Candidate-scoped claim artifacts

- Implemented `REQ-RCI-002`: release-candidate identity records whether measured/replayed/target claims carry candidate-bound artifact scope, and release admission requires that closure.
- Changed paths: `src/sentinel_edge/release/candidate.py`, `tests/test_release_candidate.py`, `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/e97a82210831b92878fff4471a6f6689c53e6f184f25a3e75aab18e8f35977aa.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_release_candidate.py -k claim_artifact_scope` (1 passed; existing warning recorded).
## 2026-08-13 — Platform mutation invalidation

- Implemented `REQ-PRE-003`: platform fact mismatches, missing facts, expired envelopes, and fixture sources cannot inherit target qualification.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/ba59ad5112540dc864b0828930d53cde13f4580bc345450b56773d91bc48382b.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_platform_envelope_v021.py` (3 passed).
## 2026-08-13 — Drift revalidation decisions

- Implemented `REQ-PRE-002`: insufficient or persistent drift is explicitly preserved, weakened, or sent to review, with no automatic retraining or silent continuation of qualified claims.
- Changed paths: `registries/requirements.yaml`, `registries/tests.yaml`, `provenance/evidence/fda4a1809a8e8140b354702395bc5044e97550fa6f08f1c096e69470e7e0142c.json`.
- Exact verification command: `.venv\Scripts\python.exe -m pytest -q tests/test_drift_governance.py` (3 passed).

## 2026-08-14 — Final UIX, simultaneous-event proof, and pinned Arm64 emulator profile

- Completed the local responsive UIX workspace against the ten supplied reference-screen families: Overview, Sites, Devices, Incident Details, AI Investigation, Policies, Reports, Deploy New Site, Firmware & Updates, and Automation, while preserving Mission Control, Benchmark Lab, Judge Proof, and the experimental Collaborative Detection surface.
- Added explicit confirmation/blast-radius handling for disruptive UI actions and retained Component 4 as the sole incident-state authority.
- Expanded `python scripts/dev.py scenario` into a machine-readable simultaneous-event proof with 24 executable invariants covering all four hazards, Tier-A reservation, wildfire wake/sleep, adaptive flood/landslide cadence, bounded queues, deferral/overload, source and sensor failure, deterministic worker crash/recovery, replay/backfill freshness protection, evidence creation, Component-4 transitions, Component-5 projection, storage/clock faults, and thermal/power policy pressure.
- Added strict aggregate-test receipts that fail closed on zero collection, skips, xfail/xpass, and record test counts/duration/evidence paths.
- Pinned the canonical Arm64 guest to `python:3.13.15-slim`, projected the exact runtime dependency set from `uv.lock` into `docker/requirements-arm64.lock.txt`, pinned ONNX Runtime to `1.28.0`, and added container image identity to Arm64 doctor/benchmark evidence.
- Verified locally: setup, client/UI tests, architecture boundaries, contract synchronization, collaboration contract/privacy/Gmail-fixture suites, the 24-invariant scenario proof, security/privacy H0 tests, and focused release-candidate tests. The final exact Docker/QEMU Arm64 matrix remains intentionally unclaimed in this sandbox because Docker/QEMU is unavailable here.

## 2026-08-14 — Machine-readable UIX conformance and strict Judge test termination

- Added `architecture/uix-screen-contract.yaml` and `scripts/generate_uix_conformance.py` so the release now verifies the implemented client against the supplied UIX specification and all ten reference mockups without treating those design mockups as runtime evidence.
- Added `qualification/uix-conformance.json`, binding the exact UIX specification digest, the ten reference-mockup digests, implementation source digests, and 21 executable UIX requirements; current result is 21/21 pass, including 20/20 H0 requirements and the optional H1 Collaborative Detection UI surface.
- Added `python scripts/dev.py uix` to the authoritative command catalogue and wired UIX conformance generation into `verify`, `gates`, `clients`, and submission-readiness generation.
- Hardened the isolated strict pytest acceptance-batch runner so a completed batch exits deterministically even if an integration test leaves a non-daemon helper thread alive; the runner still writes its machine-readable receipt and fails closed on zero collection, skips, xfail/xpass, collection errors, or test failures.
- Exact verification commands: `python scripts/dev.py uix` (pass; 9 tests), `python scripts/dev.py clients` (pass; 21 tests), focused UIX/command/strict-runner suite (16 passed), `python scripts/dev.py verify` (pass), and `python scripts/dev.py scenario` (24/24 invariants pass).
- The exact post-change Docker/QEMU `linux/arm64` submission matrix remains intentionally unclaimed in this sandbox; release admission therefore remains fail-closed until `submission-preflight` succeeds on the frozen revision in an Arm64-emulation-capable local environment.

## 2026-08-14 — Deterministic submission transcript closure

- Fixed a release-evidence nondeterminism in the simultaneous-event proof: the candidate-facing wildfire evidence item previously inherited a random UUID/default receipt time, which made the scenario transcript digest change across otherwise identical runs.
- The submission scenario now assigns a deterministic UUIDv5 evidence identity derived from the scenario and uses the fixture event time for evidence receipt, preserving the ordinary Component-4/evidence path while making the exported transcript byte-stable.
- Added a regression test that runs the complete submission scenario twice and requires identical transcript SHA-256, invariant-report SHA-256, evidence ID, and transcript bytes.
- Exact verification: `python -m pytest -q tests/test_submission_scenario_proof.py` (2 passed); two consecutive `python scripts/dev.py scenario` runs produced the same transcript file SHA-256 `060aaf89047c3ca971c5fe3db5a796e6382b53768d13882e663d450ac4afd0e5` and the generated readiness report remained byte-identical after another scenario/report cycle.

## 2026-08-14 — Interactive UIX authority path and no-egress Arm64 runner

- Converted additional reference-screen controls from decorative placeholders into explicit local interactions: Sites and Devices inspectors now have functional tabs and deep links; device filters are stateful; incident previous/next and evidence rows are interactive; Reports can save a local-only schedule; Provisioning validates required fields and saves a page-local draft; Firmware rollout controls are visibly staged; Automation preserves a real Draft/Published distinction without executing production remediation.
- Added a local Operator session shortcut and wired **Acknowledge Incident** to the existing authorized Component-5 `/v1/incidents/{hazard}/acknowledge` endpoint with CSRF and idempotency. Unsupported containment/device mutations remain staged only, and Component 4 remains the sole authoritative incident-state writer.
- Extended `architecture/uix-screen-contract.yaml` with executable H0 interaction and authority checks; the generated UIX result is now 23/23 overall and 22/22 H0.
- Hardened the canonical Docker/QEMU Arm64 runner with Docker `--network none`. Added guest kernel-namespace inspection that requires loopback-only interfaces and no default route; Arm64 doctor and benchmark lanes now fail if that below-application-layer no-egress condition is not observed.
- Exact focused verification: `python -m pytest -q tests/test_arm64_emulation_profile.py tests/test_uix_reference_screens.py tests/test_mission_control_uix.py tests/test_auth_and_commands.py tests/test_api_workflows.py` (18 passed) and `python scripts/dev.py verify` (pass).
- The exact final Docker/QEMU Arm64 matrix still must be executed on the frozen revision in an Arm64-emulation-capable local environment before release admission; no physical device or physical sensor is required.
## 2026-08-14 — Final AArch64 runtime identity, dependency closure, and benchmark instrumentation

- Reworked `python scripts/dev.py setup` so a pristine checkout becomes importable through a normal site-packages `.pth` instead of an undocumented `PYTHONPATH` override. Ordinary local Judge/demo execution can reuse an already-installed compatible environment when offline, while `submission-preflight` sets a strict mode that requires the exact hash-pinned `requirements-dev.lock.txt`.
- Added `config/arm64-python-artifacts.json` and deterministic `scripts/generate_arm64_dependency_lock.py`. The canonical Arm64 Docker build now uses an OCI-digest-pinned Python 3.13.15 base and `pip --require-hashes --only-binary=:all:` over the full Judge/test lock plus exact AArch64 NumPy, Protobuf, FlatBuffers and ONNX Runtime 1.28.0 artifacts.
- Added `src/sentinel_edge/qualification/arm64_runtime.py`: Arm64 doctor/benchmark create a real ONNX Runtime `InferenceSession`, force `CPUExecutionProvider`, execute the admitted deterministic 0.5 known-answer graph, reject provider fallback, and bind model digest/size plus the installed ONNX Runtime distribution `RECORD` and native-library hashes.
- Expanded benchmark evidence with queue/service totals, explicit heavy-workload invocation and duty-cycle accounting, scheduler decision counts, explicit `simulated` labels for thermal/power/resource policy inputs, and a separate scheduler-control-plane CPU-overhead microbenchmark measured only inside the Arm64 guest.
- Strengthened release-candidate validation so old Arm64 benchmark artifacts that lack the new known-answer/runtime identity or scheduler/workload instrumentation are not eligible for the final frozen candidate.
- Local verification completed in this environment: `verify` passed; `scenario` retained 24/24 invariants; `uix` retained 23/23 checks; Collaboration suite passed 61 tests; focused Arm/runtime/benchmark/release tests passed. A strict `test-all` attempt completed batches 1 and 2 and was still running batch 3 when the execution sandbox's per-command time limit terminated it, so no full `test-all` pass is claimed here.
- The exact final Docker/QEMU Arm64 run remains the only technical evidence action that cannot be executed inside this ChatGPT sandbox. It must be generated by `submission-preflight` on the frozen revision; no Raspberry Pi or physical sensor is required.
- Audited the generated Judge package and found that the source-export allowlist omitted `docker/`, root dependency locks, `schemas/`, `package.json`, `HACKATHON_WORKLOG.md`, `SECURITY.md`, and `CONTRIBUTING.md`. Fixed `scripts/export_source.py` and added regression checks so a public Judge package now contains the exact Arm64 reproduction inputs and submission-governance files instead of only the Python source tree.
## 2026-08-14 — Clean Judge-checkout import precedence

- Found a clean-package integrity defect during a Judge-package smoke test: a stale editable install from a different checkout could appear earlier on `sys.path` and cause the Judge commands to execute code from the wrong source tree even though the copied package itself looked valid.
- Replaced the passive checkout `.pth` with `000-sentinel-edge-checkout.pth`, which prepends only the declared source roots during standard Python site startup; legacy checkout `.pth` files are removed when possible.
- Added a fail-closed setup self-test that imports `sentinel_edge` in a fresh Python process and requires the resolved module file to be inside the current checkout's `src/` tree. The result is recorded in `.tmp/setup-environment.json`.
- Added regression coverage in `tests/test_clean_checkout_setup.py`; focused setup/preflight tests pass. A rebuilt Judge package is smoke-tested from a fresh temporary path before final packaging.

## 2026-08-14 — Isolated final Judge-package smoke verification

- Hardened `scripts/build_judge_package.py --verify-local` so the unpacked Judge package is exercised with a temporary virtual environment instead of mutating or inheriting checkout-path state in the developer interpreter.
- The smoke lane now validates that `sentinel_edge.__file__` resolves under the copied package's own `src/` tree immediately after setup, closing the stale-editable/PTH shadowing failure mode found during package audit.
- Updated `python scripts/dev.py package`: pre-candidate packaging stays fast, while an admitted frozen candidate automatically adds `--verify-local` and therefore proves the public package from a fresh copy before final distribution.
- Added focused regression tests for package-smoke isolation and admitted-candidate package behavior.

## 2026-08-14 — Exact-bound resumable strict test-all

- Extended the strict H0 `test-all` batch runner with resumable receipts so long acceptance runs can survive process/time-window interruption without restarting already completed batches.
- Reuse is fail-closed: every receipt is bound to the exact source-tree digest, setup/runtime fingerprint (Python executable/version, platform/machine, setup mode and resolved exact-lock rows), ordered test paths, and a deterministic batch signature. Any source/environment/path change clears or rejects stale receipts.
- The per-batch runner now records source/environment/signature/index metadata alongside collection, failures, skips and xfail/xpass state. Only valid nonzero-collection receipts with no skip/xfail/failure may be reused.
- `python scripts/dev.py test-all` now enables this exact-bound resume mode automatically; a fresh clone still executes every batch from scratch. Focused strict-runner regression tests pass.

## 2026-08-14 — Clean-tree export test determinism

- The resumable full acceptance run exposed a nondeterministic test assumption in `tests/test_r01_export.py`: it expected the repository to already be dirty, so it failed correctly when executed on the clean release tree.
- Reworked the test to create and remove its own explicit untracked dirty-worktree probe around `export_source.py --require-clean`. The assertion now tests the intended fail-closed behavior independent of developer workspace state.
- Focused export tests pass after the correction.
