import pytest

from sentinel_edge.evolution.delivery_catalog import DeliveryClass, DeliveryContract, DeliveryContractCatalog


def test_delivery_catalog_states_durability_coalescing_and_retry() -> None:
    catalog = DeliveryContractCatalog(contracts=tuple(DeliveryContract(
        message_type=name, delivery_class=kind, durable=kind is not DeliveryClass.TELEMETRY,
        coalescing="latest" if kind is DeliveryClass.REPLACE_LATEST else "none", retry_policy="bounded-exponential")
        for name, kind in (("incident", DeliveryClass.CRITICAL_STATE), ("telemetry", DeliveryClass.TELEMETRY))))
    assert catalog.contracts[0].durable is True
    assert catalog.contracts[1].retry_policy == "bounded-exponential"


def test_critical_state_cannot_be_nondurable() -> None:
    with pytest.raises(ValueError):
        DeliveryContract(message_type="incident", delivery_class=DeliveryClass.CRITICAL_STATE,
            durable=False, coalescing="none", retry_policy="retry")
