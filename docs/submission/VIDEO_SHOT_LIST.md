# Sentinel Edge — Video Shot List

Capture every shot from the exact frozen candidate. Do not use `docs/design/reference-mockups/` as runtime footage.

| # | Duration | Shot | Required visible truth |
|---:|---:|---|---|
| 1 | 8s | Mission Control full screen | four hazards, Research MVP warning, Arm64 emulated disclosure |
| 2 | 10s | Judge Proof / release identity | candidate ID, release profile, no physical-hardware requirement |
| 3 | 20s | Scheduler during simultaneous-event replay | running/queued/sleeping/deferred, Tier-A reservation, reasons |
| 4 | 16s | Wildfire + earthquake hazard details | simulated source mode, evidence, waveform/clip, uncertainty |
| 5 | 14s | Flood + landslide cards | missingness/coverage separate from state, cadence adaptation |
| 6 | 18s | Scenario fault/recovery proof | source outage, replay-not-fresh, recovery/reconciliation |
| 7 | 28s | Benchmark Lab | B0 111.5 ms / B1 80.5 / O1 69.0; misses 3/1/0; `simulated` label |
| 8 | 14s | Judge commands / local UI | no hardware/cloud/key requirement; Arm64 command path |
| 9 | 12s | Collaboration page | Experimental, Default OFF, separate sharing/research consent, email_unverified |
| 10 | 8s | Closing overview | candidate/repo identity, Apache-2.0, safety banner |

## Capture rules

- Keep total video under three minutes.
- No third-party copyrighted music/media unless licensed.
- Do not show tokens, OAuth credentials, private keys, private paths or restricted evidence.
- The local viewer token may be omitted from the video; judges can read it in the Judge Guide.
- Every benchmark frame must retain the `simulated` / Arm64-emulated disclaimer.
- Do not call the emulated benchmark “Raspberry Pi performance.”
- Do not imply Collaborative Detection email transport authenticates peer identity.
