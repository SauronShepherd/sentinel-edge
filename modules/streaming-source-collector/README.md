# Streaming Source Collector

The collector is the sole owner of source acquisition. It validates observations, applies entitlement and privacy policy, quarantines hostile bytes, persists idempotency state, and emits bounded observations. It does not declare or mutate incident truth.

The core is deterministic: identity is derived from source, sequence, and payload; redelivery is safe through the SQLite ingress ledger. Offline fixtures should use the same pipeline and connector contract as live sources.

Run the workspace gate from the repository root with `python scripts/dev.py gates`.
