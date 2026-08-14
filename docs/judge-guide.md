# Sentinel Edge Judge Guide

Sentinel Edge is an offline-first research monitoring and decision-support MVP. It is not an official warning authority and does not predict earthquakes or assert exact wildfire ignition coordinates.

## Five-minute tour

1. Run `python scripts/dev.py setup` to validate the local contract, registry, ADR, and architecture spine.
2. Run `python scripts/dev.py verify` for the complete offline repository verification lane.
3. Run `python scripts/dev.py doctor` to inspect host and capability state. A development host is not target-qualified.
4. Run `python scripts/dev.py demo` for the deterministic four-hazard scenario.
5. Run `python scripts/dev.py scenario` for the simultaneous-event replay and scheduler transcript.
6. Run `python scripts/dev.py benchmark-replay` to inspect the signed simulated B0/B1/O1 reference results.
7. Run `python scripts/dev.py arm64-setup` once, then `arm64-doctor`, `arm64-test`, `arm64-demo`, and `arm64-scenario` to reproduce the canonical emulated-AArch64 path.

The complete documented command surface is generated from `architecture/command-catalog.yaml` and includes:

```text
setup doctor verify format lint type governance architecture contracts plugins testkit
components clients packages compatibility generated scenario security privacy accessibility
benchmark benchmark-replay provenance docs claims aer report package backup-verify update-verify
demo test-all gates submission-preflight release-candidate
arm64-setup arm64-doctor arm64-test arm64-demo arm64-scenario arm64-benchmark
collaboration-check collaboration-demo collaboration-gmail-fixture
```

The hackathon candidate uses Docker/QEMU `linux/arm64` emulation. Fixture outputs are labelled `simulated` or `fixture`; they must not be presented as physical-device or Raspberry Pi measurements. The four hazards retain separate state, missingness, uncertainty, and safety wording. Component 4 is the sole incident-state authority.

## No-network path

The commands above use repository fixtures and do not require credentials, an account, or network access. The benchmark replay is a reference replay, not a target performance claim. Emulated Arm64 evidence establishes guest execution and deterministic comparative behavior, not Raspberry Pi performance, energy, thermal, or physical-sensor quality.

## Evidence boundary

Candidate and benchmark claims are valid only when their manifests, identities, raw artifacts, and qualification state agree. Do not upgrade `tested`, `simulated`, or `fixture` evidence to `demonstrated`, `target-qualified`, or `release-admitted` in prose or screenshots.

## Final candidate closure

After the ordinary Judge flow is green, run `python scripts/dev.py submission-preflight` on the clean final Git revision. It records every local and Arm64 command, regenerates source-bound release evidence, and writes `qualification/submission-command-matrix.json`. Then run `python scripts/dev.py release-candidate`; admission fails closed if Git identity is unavailable/dirty, the Arm64 benchmark is missing, the command matrix is stale, or claims/evidence do not bind to the same source state.
