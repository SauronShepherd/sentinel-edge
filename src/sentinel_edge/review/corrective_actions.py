"""Auditable corrective-action lifecycle for after-event reviews."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class ActionState(StrEnum):
    OPEN = "open"
    VERIFIED = "verified"
    ACCEPTED_DEBT = "accepted_debt"
    CLOSED = "closed"


@dataclass(frozen=True)
class CorrectiveAction:
    action_id: str
    owner: str
    priority: str
    due_state: str
    requirement_id: str
    test_id: str
    closure_evidence: tuple[str, ...]
    state: ActionState = ActionState.OPEN
    audit: tuple[str, ...] = ()

    def advance(self, state: ActionState, *, evidence: str | None = None) -> "CorrectiveAction":
        if state is ActionState.CLOSED and not evidence and not self.closure_evidence:
            raise ValueError("closed corrective action requires closure evidence")
        if state is ActionState.ACCEPTED_DEBT and not evidence:
            raise ValueError("accepted debt requires explicit evidence or rationale")
        if not self.owner.strip() or not self.requirement_id.strip() or not self.test_id.strip():
            raise ValueError("corrective action linkage is required")
        marker = f"{self.state.value}->{state.value}"
        if evidence:
            marker += f":{evidence}"
        return replace(self, state=state, audit=(*self.audit, marker), closure_evidence=(*self.closure_evidence, evidence) if evidence else self.closure_evidence)
