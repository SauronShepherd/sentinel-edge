"""Low-cardinality metrics for Collaborative Detection."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field

_ALLOWED_LABELS = {
    "hazard": {"wildfire", "earthquake", "flood", "landslide"},
    "result": {"accepted", "rejected", "sent", "failed", "expired", "duplicate"},
    "validation_state": {"admitted", "context_only", "rejected"},
    "transport_trust": {"fixture_qualified", "email_unverified", "authenticated_peer", "rejected"},
    "kind": {"signal", "transport_message"},
    "action": {"no_action", "context_only", "create_review_incident", "update_incident", "multi_node_trigger_simulated"},
}


@dataclass
class CollaborationMetrics:
    counters: Counter[tuple[str, tuple[tuple[str, str], ...]]] = field(default_factory=Counter)
    gauges: dict[str, float] = field(default_factory=dict)

    def inc(self, name: str, **labels: str) -> None:
        for key, value in labels.items():
            if key not in _ALLOWED_LABELS or value not in _ALLOWED_LABELS[key]:
                raise ValueError("COLLABORATION_METRIC_HIGH_CARDINALITY_OR_UNKNOWN_LABEL")
        self.counters[(name, tuple(sorted(labels.items())))] += 1

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = float(value)

    def snapshot(self) -> dict[str, object]:
        items = []
        for (name, labels), value in sorted(self.counters.items()):
            items.append({"name": name, "labels": dict(labels), "value": value})
        return {"counters": items, "gauges": dict(sorted(self.gauges.items()))}
