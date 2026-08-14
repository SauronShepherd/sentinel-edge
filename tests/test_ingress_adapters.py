from datetime import datetime, timezone

import pytest

from sentinel_edge.collector import HttpIngressAdapter, IngressRejected, MqttIngressAdapter, WebSocketIngressAdapter
from sentinel_edge.domain.models import SourceMode


def payload() -> dict:
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc).isoformat()
    return {
        "schema_version": "2.0.0", "hazard": "earthquake", "sequence": 4,
        "observed_at": now, "received_at": now,
        "values": {"accel_x": 0.1, "accel_y": 0.0, "accel_z": 1.0},
        "units": {"accel_x": "g", "accel_y": "g", "accel_z": "g"},
    }


def test_http_websocket_and_mqtt_share_normalized_live_contract() -> None:
    adapters = (
        HttpIngressAdapter().accept(payload(), source_id="phone-1"),
        WebSocketIngressAdapter().accept(payload(), source_id="phone-1"),
        MqttIngressAdapter().accept(payload(), source_id="phone-1", topic="sentinel/imu", qos=1),
    )
    assert [tuple(sorted(item.observation.values.items())) for item in adapters] == [
        (("accel_x", 0.1), ("accel_y", 0.0), ("accel_z", 1.0)),
    ] * 3
    assert all(item.observation.source_mode is SourceMode.LIVE for item in adapters)
    assert [item.observation.source_lineage for item in adapters] == ["ingress:http", "ingress:websocket", "ingress:mqtt"]


def test_ingress_rejects_bad_content_topic_qos_and_oversized_payload() -> None:
    with pytest.raises(IngressRejected, match="application/json"):
        HttpIngressAdapter().accept(payload(), source_id="s", content_type="text/plain")
    with pytest.raises(IngressRejected, match="topic"):
        MqttIngressAdapter().accept(payload(), source_id="s", topic="")
    with pytest.raises(IngressRejected, match="QoS"):
        MqttIngressAdapter().accept(payload(), source_id="s", topic="x", qos=3)
    with pytest.raises(IngressRejected, match="byte bound"):
        WebSocketIngressAdapter(max_bytes=10).accept(payload(), source_id="s")


def test_ingress_rejects_nan_and_invalid_observations() -> None:
    with pytest.raises(IngressRejected, match="finite JSON"):
        HttpIngressAdapter().accept('{"values":{"x":NaN}}', source_id="s")
    with pytest.raises(IngressRejected, match="validation"):
        WebSocketIngressAdapter().accept({"values": {}}, source_id="s")
