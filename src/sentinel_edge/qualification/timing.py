"""Typed event/ingest/decision latency decomposition."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LatencyDecomposition(BaseModel):
    """A single source's time chain, with no collapsed end-to-end-only metric."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    event_time: datetime
    ingest_time: datetime
    decision_time: datetime
    event_to_ingest_ms: float = Field(ge=0.0)
    ingest_to_decision_ms: float = Field(ge=0.0)
    event_to_decision_ms: float = Field(ge=0.0)


def decompose_latency(source_id: str, row: dict[str, object]) -> LatencyDecomposition:
    """Validate and derive all three latency legs from scenario timing output."""
    try:
        event_time = datetime.fromisoformat(str(row["capture_at"]))
        ingest_time = datetime.fromisoformat(str(row["ingest_at"]))
        decision_time = datetime.fromisoformat(str(row["decision_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("timing row must contain ISO capture_at, ingest_at, and decision_at") from exc
    event_to_ingest = (ingest_time - event_time).total_seconds() * 1000
    ingest_to_decision = (decision_time - ingest_time).total_seconds() * 1000
    event_to_decision = (decision_time - event_time).total_seconds() * 1000
    if min(event_to_ingest, ingest_to_decision, event_to_decision) < 0:
        raise ValueError("event, ingest, and decision times must be monotonic")
    return LatencyDecomposition(
        source_id=source_id,
        event_time=event_time,
        ingest_time=ingest_time,
        decision_time=decision_time,
        event_to_ingest_ms=event_to_ingest,
        ingest_to_decision_ms=ingest_to_decision,
        event_to_decision_ms=event_to_decision,
    )


def build_latency_report(timing_metrics: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        source_id: decompose_latency(source_id, row).model_dump(mode="json")
        for source_id, row in sorted(timing_metrics.items())
    }
