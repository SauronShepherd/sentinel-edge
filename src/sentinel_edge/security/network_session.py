"""Session epoch guard for network exposure-mode changes."""

from dataclasses import dataclass
from enum import StrEnum


class NetworkMode(StrEnum):
    LOCAL_ONLY = "local_only"
    TRUSTED_LAN = "trusted_lan"
    SERVICE = "service"


@dataclass(frozen=True)
class SessionLease:
    principal_id: str
    epoch: int


class NetworkModeSessionGuard:
    def __init__(self, mode: NetworkMode = NetworkMode.LOCAL_ONLY) -> None:
        self.mode = mode
        self.epoch = 0

    def issue(self, principal_id: str) -> SessionLease:
        if not principal_id.strip():
            raise ValueError("principal_id must not be blank")
        return SessionLease(principal_id, self.epoch)

    def change_mode(self, mode: NetworkMode) -> int:
        if mode is not self.mode:
            self.mode = mode
            self.epoch += 1
        return self.epoch

    def authorize_write(self, lease: SessionLease) -> None:
        if lease.epoch != self.epoch:
            raise PermissionError("network mode changed; authentication revalidation required")

