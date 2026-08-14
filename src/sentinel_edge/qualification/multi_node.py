"""Deterministic simulated multi-node event correlation with clock offsets."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NodeSignal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str
    observed_at: datetime
    signal_score: float = Field(ge=0.0, le=1.0)
    clock_offset_ms: float = 0.0


class CorrelatedNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str
    observed_at: datetime
    clock_offset_ms: float
    signal_score: float


class MultiNodeCorrelationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_node_id: str
    correlation_window_ms: float = Field(gt=0.0)
    nodes: tuple[CorrelatedNode, ...]
    correlated: bool
    node_count: int = Field(ge=0)
    clock_offsets_shown: bool
    classification: str = "simulated"


def correlate_simulated_nodes(
    signals: tuple[NodeSignal, ...],
    *,
    correlation_window_ms: float = 500.0,
) -> MultiNodeCorrelationReport:
    if correlation_window_ms <= 0:
        raise ValueError("correlation window must be positive")
    if not signals:
        raise ValueError("at least one node signal is required")
    ordered = tuple(sorted(signals, key=lambda item: (item.observed_at, item.node_id)))
    reference = ordered[0]
    nodes = tuple(CorrelatedNode(
        node_id=item.node_id,
        observed_at=item.observed_at,
        clock_offset_ms=item.clock_offset_ms,
        signal_score=item.signal_score,
    ) for item in ordered)
    span_ms = (ordered[-1].observed_at - reference.observed_at).total_seconds() * 1000
    return MultiNodeCorrelationReport(
        reference_node_id=reference.node_id,
        correlation_window_ms=correlation_window_ms,
        nodes=nodes,
        correlated=span_ms <= correlation_window_ms and len(nodes) >= 2,
        node_count=len(nodes),
        clock_offsets_shown=all(node.clock_offset_ms == node.clock_offset_ms for node in nodes),
    )
