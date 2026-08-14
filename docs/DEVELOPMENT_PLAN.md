# Development plan after v0.21.0

1. Capture an observed Raspberry Pi 5 runtime envelope with exact board, EEPROM/bootloader, firmware, kernel, OS/root, runtime, provider, driver and hardening identities.
2. Acquire publisher-origin Arm64 wheels and rehearse the exact no-index installation on that qualified target image.
3. Execute the admitted ONNX model package with the exact target runtime/provider and run the cold/session branch/shape/output known-answer suite before service start.
4. Capture a physical IMU and camera path using the signed signal-chain profiles; qualify timestamps, effective rate, anti-aliasing, gaps, clipping and saturation.
5. Commission deployed sensors with site, mount, calibration, datum/baseline, configuration, model and explicit evidence-window identities.
6. Renew model-quality evidence against the exact physical signal, preprocessing, graph, platform envelope and target runtime package.
7. Run the signed confirmatory B0/B1/O1 plan with valid power, thermal, memory, network, host-envelope and complete-node energy evidence.
8. Obtain independent builder, security, privacy and accessibility evidence and close the remaining H0 requirements without upgrading fixtures to target verification.

## Emulated Arm64 hackathon profile

The active candidate uses the single `docker-qemu` `linux/arm64` profile documented in `config/arm64-emulation.yaml`. Run the project-facing commands through `scripts/dev.py`; report host and guest identities separately. Deterministic camera, IMU, hydrology, and landslide fixtures enter through Component 1 contracts and remain visibly simulated. Emulation may establish software execution and comparative workload evidence, never Raspberry Pi performance, physical energy/thermal, or physical-sensor quality.

Canonical command sequence:

```text
python scripts/dev.py arm64-setup
python scripts/dev.py arm64-doctor
python scripts/dev.py arm64-test
python scripts/dev.py arm64-demo
python scripts/dev.py arm64-scenario
python scripts/dev.py arm64-benchmark
```

## Optional H1/S8 collaborative detection extension

The proposed Collaborative Detection extension (`SE-COLLAB-CODEX-001`) is tracked as a disabled, additive workstream. It must not alter H0 behavior or require Gmail, credentials, or network access.

1. **Contracts and policy:** land the versioned correlation-domain, signal, consent, envelope, and decision contracts; enforce the hazard-specific observation vocabulary and the rule that research consent requires operational sharing.
2. **Local opt-in:** add consent auditing, privacy transformation, material-event signal creation, bounded queueing, and a deterministic fixture publisher. Sharing and research consent remain independent and default OFF.
3. **Component-4 correlation:** admit normalized Component-1 envelopes, reject replay/expiry/domain mismatches, count one contribution per peer, and emit explainable review/simulated decisions. Component 4 remains the only incident-state writer.
4. **Experimental email:** add replaceable MIME/SMTP and Gmail-client abstractions behind fake offline fixtures; email remains `email_unverified` and cannot create trusted multi-node verification.
5. **REST/UI and safety:** expose bounded status/consent/evidence projections without secrets or raw MIME; demonstrate that disabling collaboration restores the H0-capable path.

Current implementation state: contract slice implemented and tested; transport, correlation, REST/UI, and target qualification remain planned. Capability status must not exceed executable evidence.
