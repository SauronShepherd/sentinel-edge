import json

import pytest

from sentinel_edge.evolution.wire import WireBoundaryPolicy
from sentinel_edge.security import canonical_json_bytes


def policy() -> WireBoundaryPolicy:
    return WireBoundaryPolicy(allowed={"component-1": {"incident": {"critical_state"}, "metric": {"telemetry"}}})


def test_wire_boundary_binds_digest_delivery_and_producer() -> None:
    raw = policy().encode(contract="1.0", payload_type="incident", delivery_class="critical_state", producer_component="component-1", producer_identity="node-a", idempotency_key="i-1", aggregate_key="incident-1", aggregate_version=1, producer_sequence=1, payload={"state": "suspected"})
    assert policy().validate_raw(raw).payload_type == "incident"
    forged = json.loads(raw)
    forged["payload"] = {"state": "confirmed"}
    with pytest.raises(ValueError, match="digest"):
        policy().validate_raw(canonical_json_bytes(forged))
    forged = json.loads(raw)
    forged["producer_component"] = "component-2"
    with pytest.raises(ValueError, match="producer"):
        policy().validate_raw(canonical_json_bytes(forged))


def test_wire_boundary_rejects_unknown_major_and_semantics() -> None:
    raw = policy().encode(contract="2.0", payload_type="incident", delivery_class="critical_state", producer_component="component-1", producer_identity="node-a", idempotency_key="i-1", aggregate_key="incident-1", aggregate_version=1, producer_sequence=1, payload={})
    with pytest.raises(ValueError, match="major"):
        policy().validate_raw(raw)
    raw = policy().encode(contract="1.0", payload_type="incident", delivery_class="critical_state", producer_component="component-1", producer_identity="node-a", idempotency_key="i-1", aggregate_key="incident-1", aggregate_version=1, producer_sequence=1, payload={})
    item = json.loads(raw)
    item["delivery_class"] = "telemetry"
    with pytest.raises(ValueError, match="delivery"):
        policy().validate_raw(canonical_json_bytes(item))
