# Sentinel Edge — Sub-Three-Minute Video Script

**Target duration:** 2:35–2:50. English narration or English subtitles. Use only the frozen candidate and candidate-bound numbers.

## 0:00–0:18 — Problem + disclosure

**Visual:** Mission Control overview with all four hazard cards and the persistent bottom safety banner.

**Narration:**

> “Sentinel Edge is an offline-first Physical AI platform that runs wildfire, earthquake, flood and landslide monitoring on one constrained Arm64 edge node. The hackathon candidate uses reproducible AArch64 emulation and deterministic simulated sensor streams. This is a research MVP, not an official warning system, and these are not Raspberry Pi performance measurements.”

**Overlay:** `ARM64 EMULATED · DETERMINISTIC SIMULATED SENSORS · RESEARCH MVP`

## 0:18–0:48 — Why the orchestrator matters

**Visual:** Mission Control scheduler panel. Trigger simultaneous-event replay; show Running / Queued / Sleeping / Deferred and reason codes.

**Narration:**

> “The central optimization is the Arm AI Orchestrator. Instead of letting four fixed-rate applications contend blindly, Sentinel schedules validated jobs by criticality and deadline. Earthquake work receives reserved Tier-A service, wildfire heavy inference wakes only when needed, and flood and landslide cadence adapts while queues and maximum deferral stay bounded.”

**Overlay:** `Tier A reserved · bounded queues · wake/sleep · adaptive cadence`

## 0:48–1:18 — Four physical-AI paths

**Visual:** Cycle through the four hazard cards and Incident detail.

**Narration:**

> “Wildfire uses simulated camera frames with persistence, ambiguous-negative handling and evidence clips. Earthquake consumes a fixed-rate three-axis IMU stream, fires a deterministic trigger and preserves the waveform. Flood uses rainfall, water level and rate-of-rise with typed missingness. Landslide combines rainfall, soil, tilt and vibration indicators. Every fixture enters through the normal Component-1 observation contract; only Component 4 can mutate incident lifecycle state.”

**Overlay:** `4 hazards · normal ObservationV2 path · Component 4 sole authority`

## 1:18–1:42 — Faults, recovery and truthfulness

**Visual:** Scenario/Judge Proof showing source outage, degraded coverage, replay/backfill guard and worker recovery.

**Narration:**

> “The deterministic scenario also injects source and sensor failures, clock and storage pressure, and worker recovery. Coverage degrades visibly, and replay or backfill is never promoted into fresh evidence. Missing data cannot silently become ‘safe.’”

**Overlay:** `FAIL VISIBLE · REPLAY ≠ FRESH · COVERAGE ≠ HAZARD STATE`

## 1:42–2:15 — B0/B1/O1 benchmark

**Visual:** Benchmark Lab with all three variant cards and guardrail panel.

**Narration:**

> “For optimization proof, B0 is the naive fixed-rate baseline, B1 adds the optimized runtime profile at the same offered cadence, and O1 adds the orchestrator. On the same deterministic Arm64-emulated opportunity schedule, median semantic end-to-end latency moves from 111.5 milliseconds in B0, to 80.5 in B1, to 69.0 in O1. Deadline misses fall from three, to one, to zero, with the declared quality guardrails passing.”

**Overlay:** `SIMULATED / ARM64-EMULATED EVIDENCE` then `B0 111.5 ms / 3 misses → B1 80.5 / 1 → O1 69.0 / 0`

## 2:15–2:32 — Judgeability + collaboration

**Visual:** Judge Proof, then Collaboration page with Default OFF / Experimental.

**Narration:**

> “Judges can run setup, demo, scenario, gates and benchmark replay without hardware, accounts or API keys, then reproduce the Arm64 guest path through Docker and QEMU. Optional Collaborative Detection is off by default, shares only privacy-coarsened derived signals, and treats email peers as unverified.”

**Overlay:** `NO CLOUD · NO API KEY · NO PHYSICAL SENSOR · COLLABORATION DEFAULT OFF`

## 2:32–2:45 — Close

**Visual:** Overview/Judge Proof with repository/candidate identity once frozen.

**Narration:**

> “Sentinel Edge shows that multi-hazard Physical AI can be orchestrated transparently on Arm, with efficiency, evidence, uncertainty and safety boundaries visible at the same time.”

**Overlay:** `Sentinel Edge · Physical AI · Apache-2.0`
