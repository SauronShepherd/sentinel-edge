"""Correction-window decisions for late remote data."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CorrectionAction(StrEnum):
    LIVE = "live"
    HISTORY_ONLY = "history_only"
    REJECT = "reject"


class CorrectionWindowPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_lateness_seconds: float = Field(ge=0.0)
    future_tolerance_seconds: float = Field(ge=0.0, default=0.0)


class CorrectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_time: datetime
    received_at: datetime
    action: CorrectionAction
    retroactive_notification_allowed: bool
    reason_codes: tuple[str, ...]


def evaluate_correction_window(event_time: datetime, received_at: datetime, policy: CorrectionWindowPolicy) -> CorrectionDecision:
    delay = (received_at - event_time).total_seconds()
    if delay < -policy.future_tolerance_seconds:
        return CorrectionDecision(event_time=event_time, received_at=received_at, action=CorrectionAction.REJECT, retroactive_notification_allowed=False, reason_codes=("event_time_in_future",))
    if delay > policy.max_lateness_seconds:
        return CorrectionDecision(event_time=event_time, received_at=received_at, action=CorrectionAction.HISTORY_ONLY, retroactive_notification_allowed=False, reason_codes=("correction_window_exceeded", "history_evidence_only"))
    return CorrectionDecision(event_time=event_time, received_at=received_at, action=CorrectionAction.LIVE, retroactive_notification_allowed=True, reason_codes=("within_correction_window",))

