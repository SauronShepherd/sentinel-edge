from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RestoreAuthorization:
    actor: str
    reason: str
    target_node: str
    target_namespace: str
    policy_version: str

    def validate(self, *, expected_node: str, expected_namespace: str) -> None:
        if not all(value.strip() for value in (self.actor, self.reason, self.target_node, self.target_namespace, self.policy_version)):
            raise PermissionError("restore authorization fields are required")
        if self.target_node != expected_node or self.target_namespace != expected_namespace:
            raise PermissionError("restore authorization target mismatch")
