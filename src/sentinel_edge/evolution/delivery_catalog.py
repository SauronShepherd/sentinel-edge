"""Durability/coalescing/retry catalog for active boundary messages."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DeliveryClass(StrEnum):
    CRITICAL_STATE = "critical_state"
    REPLAYABLE_COMPUTE = "replayable_compute"
    REPLACE_LATEST = "replace_latest"
    TELEMETRY = "telemetry"


class DeliveryContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message_type: str
    delivery_class: DeliveryClass
    durable: bool
    coalescing: str
    retry_policy: str

    @model_validator(mode="after")
    def validate_contract(self) -> "DeliveryContract":
        if not self.message_type.strip() or not self.coalescing.strip() or not self.retry_policy.strip():
            raise ValueError("delivery catalog fields are required")
        if self.delivery_class is DeliveryClass.CRITICAL_STATE and not self.durable:
            raise ValueError("critical state messages must be durable")
        return self


class DeliveryContractCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contracts: tuple[DeliveryContract, ...]

    @model_validator(mode="after")
    def validate_catalog(self) -> "DeliveryContractCatalog":
        if not self.contracts or len({item.message_type for item in self.contracts}) != len(self.contracts):
            raise ValueError("catalog requires unique active message contracts")
        return self
