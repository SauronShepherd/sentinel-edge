# Sentinel Edge hackathon limitations

Sentinel Edge is a research monitoring and decision-support MVP, not an official emergency-warning system or safety-certified instrument.

## Hardware evidence

- The current hackathon profile does not claim physical Raspberry Pi 5 validation.
- No physical camera, IMU, or environmental-sensor validation is claimed.
- Raspberry Pi 5 remains a reference deployment target, not the platform from which current benchmark numbers are reported.
- No physical energy, power, thermal, throttling, or field-calibration measurement is claimed.
- Emulator wall-clock, CPU-time, and RSS observations describe only the declared Arm64-emulated guest environment.

## Hazard semantics

- The system does not predict earthquakes before rupture.
- A monocular camera does not establish an exact wildfire ignition coordinate.
- Flood and landslide H0 paths are bounded deterministic monitoring paths; they are not universal physical forecasts.
- Missing or stale evidence weakens coverage/trust and is never treated as proof of safety.

## Collaborative Detection

Collaborative Detection is optional H1/S8 functionality and is disabled by default. Email transport is experimental and `email_unverified` is not cryptographic proof of peer identity. Simulated or email-based contributions must not be presented as trusted multi-node confirmation. Raw sensor media is not shared by the v0.1 collaboration contract.
