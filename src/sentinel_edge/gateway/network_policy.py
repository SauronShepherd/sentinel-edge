"""Deterministic service exposure profiles.

This is configuration policy only; it does not imply that a target host has
proved OS-level isolation or firewall enforcement.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class ExposureProfile(StrEnum):
    LOCAL_ONLY = "local_only"
    TRUSTED_LAN = "trusted_lan"
    SERVICE = "service"
    JUDGE = "judge"
    BENCHMARK = "benchmark"


_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


class NetworkExposurePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: ExposureProfile
    bind_host: str
    auth_required: bool
    tls_required: bool
    egress_allowed: bool

    @model_validator(mode="after")
    def validate_profile(self) -> "NetworkExposurePolicy":
        host = self.bind_host.strip().lower()
        if not host:
            raise ValueError("bind_host must not be blank")
        loopback = host in _LOOPBACK
        if self.profile in {ExposureProfile.LOCAL_ONLY, ExposureProfile.JUDGE, ExposureProfile.BENCHMARK}:
            if not loopback or not self.auth_required or self.tls_required or self.egress_allowed:
                raise ValueError("restricted profile requires loopback, auth, no TLS termination, and no egress")
        elif self.profile is ExposureProfile.TRUSTED_LAN:
            if loopback or not self.auth_required or not self.tls_required or self.egress_allowed:
                raise ValueError("trusted_lan requires non-loopback bind, auth, TLS, and no egress")
        elif self.profile is ExposureProfile.SERVICE:
            if loopback or not self.auth_required or not self.tls_required:
                raise ValueError("service requires non-loopback bind, auth, and TLS")
        return self

