"""Crash/duplicate delivery evidence for durable idempotent mutation."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CrashPoint(StrEnum):
    BEFORE_COMMIT = "before_commit"
    AFTER_COMMIT_BEFORE_ACK = "after_commit_before_ack"
    AFTER_ACK = "after_ack"


class CrashMatrixRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    crash_point: CrashPoint
    delivery_attempts: int = Field(ge=1)
    effective_mutations: int = Field(ge=0)
    eventual_converged: bool

    @model_validator(mode="after")
    def validate_row(self) -> "CrashMatrixRow":
        if self.eventual_converged and self.effective_mutations != 1:
            raise ValueError("converged duplicate delivery must have one effective mutation")
        return self


class CrashMatrixReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message_contract: str
    producer_outbox: bool
    consumer_inbox: bool
    rows: tuple[CrashMatrixRow, ...]

    @model_validator(mode="after")
    def validate_report(self) -> "CrashMatrixReport":
        if not self.message_contract.strip() or not self.producer_outbox or not self.consumer_inbox:
            raise ValueError("durable outbox/inbox semantics are required")
        if {row.crash_point for row in self.rows} != set(CrashPoint):
            raise ValueError("crash matrix must cover every crash point")
        return self
