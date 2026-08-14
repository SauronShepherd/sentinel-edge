"""Separate immutable original-decision and current reevaluation views."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionReconstruction:
    decision_id: str
    original_context: dict[str, Any]
    current_context: dict[str, Any]
    original_conclusion: str
    current_conclusion: str

    def as_audit_view(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "original_decision": {"context": dict(self.original_context), "conclusion": self.original_conclusion},
            "current_reevaluation": {"context": dict(self.current_context), "conclusion": self.current_conclusion},
            "historical_context_rewritten": False,
        }
