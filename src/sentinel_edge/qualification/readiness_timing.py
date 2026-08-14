"""Boot/recovery readiness timing transcript."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReadinessTiming(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    boot_started_at: datetime
    ready_at: datetime
    recovery_started_at: datetime
    recovery_ready_at: datetime
    readiness_gates: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_timing(self) -> "ReadinessTiming":
        if self.ready_at < self.boot_started_at:
            raise ValueError("ready_at cannot precede boot start")
        if self.recovery_ready_at < self.recovery_started_at:
            raise ValueError("recovery_ready_at cannot precede recovery start")
        if any(not gate.strip() for gate in self.readiness_gates):
            raise ValueError("readiness gate names must not be blank")
        return self

    @property
    def boot_to_ready_seconds(self) -> float:
        return (self.ready_at - self.boot_started_at).total_seconds()

    @property
    def recovery_to_ready_seconds(self) -> float:
        return (self.recovery_ready_at - self.recovery_started_at).total_seconds()

    def transcript(self) -> dict[str, object]:
        return {
            "boot_to_ready_seconds": self.boot_to_ready_seconds,
            "recovery_to_ready_seconds": self.recovery_to_ready_seconds,
            "readiness_gates": list(self.readiness_gates),
        }

