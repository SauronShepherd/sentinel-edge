from sentinel_edge.storage.telemetry_schema import TelemetrySchemaPin, compare_telemetry_schema_pins


def pin(**overrides):
    data = {"sdk_name": "opentelemetry", "sdk_version": "1.0", "semantic_convention_version": "1.27",
        "schema_digest": "a" * 64, "field_types": {"latency_ms": "float"}}
    data.update(overrides)
    return TelemetrySchemaPin(**data)


def test_telemetry_schema_pin_rejects_dependency_drift() -> None:
    compatible, _ = compare_telemetry_schema_pins(pin(), pin())
    assert compatible is True
    compatible, reasons = compare_telemetry_schema_pins(pin(), pin(field_types={"latency_ms": "string"}))
    assert compatible is False
    assert "telemetry_field_type_drift" in reasons
