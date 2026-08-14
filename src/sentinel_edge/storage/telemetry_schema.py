"""Pinned telemetry SDK and semantic-convention compatibility contract."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TelemetrySchemaPin(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sdk_name: str
    sdk_version: str
    semantic_convention_version: str
    schema_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    field_types: dict[str, str]

    @model_validator(mode="after")
    def validate_pin(self) -> "TelemetrySchemaPin":
        if any(not value.strip() for value in (self.sdk_name, self.sdk_version, self.semantic_convention_version)):
            raise ValueError("telemetry SDK and semantic convention pins are required")
        if not self.field_types:
            raise ValueError("telemetry schema fields are required")
        return self


def compare_telemetry_schema_pins(expected: TelemetrySchemaPin, actual: TelemetrySchemaPin) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if expected.sdk_name != actual.sdk_name or expected.sdk_version != actual.sdk_version:
        reasons.append("telemetry_sdk_drift")
    if expected.semantic_convention_version != actual.semantic_convention_version:
        reasons.append("semantic_convention_drift")
    if expected.schema_digest != actual.schema_digest:
        reasons.append("telemetry_schema_digest_drift")
    if expected.field_types != actual.field_types:
        reasons.append("telemetry_field_type_drift")
    return not reasons, tuple(sorted(reasons or ["telemetry_schema_compatible"]))
