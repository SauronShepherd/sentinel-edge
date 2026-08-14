# Sentinel Edge — Candidate Screenshot Plan

All submission screenshots MUST be captured from the exact frozen running candidate and registered in `provenance/submission-media/`. The PNGs under `docs/design/reference-mockups/` are design references only and MUST NOT be submitted as product evidence.

## Required captures

1. **Mission Control — all four hazards**
   - Wildfire, Earthquake, Flood and Landslide visible together.
   - Arm64 emulated disclosure and Research MVP warning visible.
   - Source/coverage/uncertainty labels readable.

2. **Scheduler activity / Tier-A reservation**
   - Running, queued, sleeping and deferred states.
   - Earthquake Tier-A reservation or reason code.
   - Bounded/deferred workload explanation.

3. **Wildfire hero proof**
   - Possible/persistent smoke state.
   - Simulated camera source label.
   - Persistence/abstention/evidence clip context.

4. **Earthquake hero proof**
   - Earthquake-like shaking wording, never prediction.
   - Simulated three-axis IMU source.
   - Clock quality, waveform evidence and reserved dispatch.

5. **Flood / landslide bounded paths**
   - Rain/water/rate-of-rise and movement indicators.
   - Missing/stale/partial coverage treatment.
   - Adaptive cadence reason.

6. **Health and coverage separate from hazard state**
   - One degraded source or partial coverage example.
   - No “safe because detector did not fire” implication.

7. **Benchmark Lab**
   - B0 = 111.5 ms / 3 misses.
   - B1 = 80.5 ms / 1 miss.
   - O1 = 69.0 ms / 0 misses.
   - Quality guardrails PASS.
   - `simulated` / Arm64-emulated disclosure visible.

8. **Judge Proof**
   - Twelve G0 packs.
   - H0 240/240 closure.
   - Arm64 execution profile.
   - Physical hardware/sensors not required.

9. **Incident detail / evidence authority**
   - Timeline/evidence/review.
   - Component 4 sole incident authority wording.
   - Source mode and uncertainty visible.

10. **Collaborative Detection**
    - Experimental + Default OFF.
    - Separate sharing/research consent.
    - Fixture-qualified simulated peers vs `email_unverified` distinction.

## Manifest fields per screenshot

Record at least:

- screenshot ID and filename;
- candidate ID and commit;
- captured route/screen;
- UTC capture timestamp;
- source mode(s);
- claim IDs visible in the screenshot;
- SHA-256;
- privacy/rights review state;
- note confirming whether any value is simulated/replayed.

> **Benchmark truth boundary:** all B0/B1/O1 values in the capture plan are simulated Arm64-emulated comparative evidence, **not Raspberry Pi 5 performance measurements**.
