from datetime import datetime, timezone

from sentinel_edge.domain.models import CriticalityTier, HazardKind, ResourceSnapshot, WorkloadSpec
from sentinel_edge.runtime import OpportunityLedger, WorkloadScheduler


def spec(name: str, tier: CriticalityTier, memory: int = 16) -> WorkloadSpec:
    return WorkloadSpec(workload_id=name, hazard=HazardKind.EARTHQUAKE if tier == CriticalityTier.A_IMMEDIATE else HazardKind.FLOOD,
                        tier=tier, period_ms=100, deadline_ms=1000, max_deferral_ms=1000,
                        estimated_cost_ms=10, memory_mb=memory, profile_id="test")


def test_tier_a_precedes_lower_tiers() -> None:
    scheduler = WorkloadScheduler()
    scheduler.register(spec("low", CriticalityTier.C_TIMELY))
    scheduler.register(spec("seismic", CriticalityTier.A_IMMEDIATE))
    now = datetime.now(timezone.utc)
    scheduler.submit("low", {}, now)
    scheduler.submit("seismic", {}, now)
    resources = ResourceSnapshot(cpu_pressure=0.2,memory_pressure=0.2,io_pressure=0.2,temperature_c=45,available_memory_mb=128)
    assert scheduler.dispatch(resources).workload.workload_id == "seismic"


def test_reserve_blocks_lower_tier_but_not_tier_a() -> None:
    scheduler = WorkloadScheduler(tier_a_reserve_memory_mb=64)
    scheduler.register(spec("low", CriticalityTier.C_TIMELY, memory=40))
    scheduler.register(spec("seismic", CriticalityTier.A_IMMEDIATE, memory=16))
    now = datetime.now(timezone.utc)
    scheduler.submit("low", {}, now)
    scheduler.submit("seismic", {}, now)
    resources = ResourceSnapshot(cpu_pressure=0.2,memory_pressure=0.2,io_pressure=0.2,temperature_c=45,available_memory_mb=80)
    assert scheduler.dispatch(resources).workload.workload_id == "seismic"
    assert scheduler.dispatch(resources) is None


def test_external_media_backlog_cannot_displace_tier_a_or_tier_b() -> None:
    scheduler = WorkloadScheduler(queue_limit=32, tier_a_reserve_memory_mb=64)
    scheduler.register(spec("multimodal-backlog", CriticalityTier.C_TIMELY, memory=40))
    scheduler.register(spec("urgent-hot-path", CriticalityTier.B_URGENT, memory=16))
    scheduler.register(spec("seismic-hot-path", CriticalityTier.A_IMMEDIATE, memory=16))
    now = datetime.now(timezone.utc)
    for index in range(8):
        scheduler.submit("multimodal-backlog", {"media_index": index}, now)
    scheduler.submit("urgent-hot-path", {"physical": True}, now)
    scheduler.submit("seismic-hot-path", {"physical": True}, now)
    resources = ResourceSnapshot(cpu_pressure=0.2, memory_pressure=0.2, io_pressure=0.2,
                                 temperature_c=45, available_memory_mb=80)
    first = scheduler.dispatch(resources)
    assert first.workload.workload_id == "seismic-hot-path"
    scheduler.complete(first)
    second = scheduler.dispatch(resources)
    assert second.workload.workload_id == "urgent-hot-path"
    assert scheduler.snapshot().queued or scheduler.snapshot().deferred


def test_unknown_tier_a_interference_is_serialized() -> None:
    scheduler = WorkloadScheduler()
    scheduler.register(spec("seismic", CriticalityTier.A_IMMEDIATE))
    scheduler.register(spec("unknown-heavy", CriticalityTier.A_IMMEDIATE))
    now = datetime.now(timezone.utc)
    first = scheduler.submit("seismic", {}, now)
    second = scheduler.submit("unknown-heavy", {}, now)
    resources = ResourceSnapshot(cpu_pressure=0.2, memory_pressure=0.2, io_pressure=0.2,
                                 temperature_c=45, available_memory_mb=128)
    assert scheduler.dispatch(resources).job_id == first.job_id
    assert scheduler.dispatch(resources) is None
    assert "unknown_tier_a_interference_serialized" in second.reason_codes


def test_declared_safe_tier_a_pair_can_co_run() -> None:
    scheduler = WorkloadScheduler(known_safe_interference_pairs={("seismic", "known-safe")})
    scheduler.register(spec("seismic", CriticalityTier.A_IMMEDIATE))
    scheduler.register(spec("known-safe", CriticalityTier.A_IMMEDIATE))
    now = datetime.now(timezone.utc)
    scheduler.submit("seismic", {}, now)
    scheduler.submit("known-safe", {}, now)
    resources = ResourceSnapshot(cpu_pressure=0.2, memory_pressure=0.2, io_pressure=0.2,
                                 temperature_c=45, available_memory_mb=128)
    assert scheduler.dispatch(resources) is not None
    assert scheduler.dispatch(resources) is not None


def test_opportunity_ledger_supports_explicit_terminal_outcomes() -> None:
    from uuid import uuid4
    from sentinel_edge.domain.models import OpportunityDisposition
    from sentinel_edge.runtime import OpportunityLedger
    ledger = OpportunityLedger()
    record = ledger.offer(
        workload_id="flood-evaluate", hazard=HazardKind.FLOOD,
        scheduled_release_at=datetime.now(timezone.utc), captured_at=None,
        correlation_id=uuid4(),
    )
    ledger.mark_terminal(record.opportunity_id, OpportunityDisposition.EXPIRED, 10, "deadline_window_elapsed")
    assert ledger.counts()["expired"] == 1
    assert ledger.reconcile()["balanced"] is True


def test_opportunity_schedule_is_signed_and_tamper_evident() -> None:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from uuid import uuid4
    ledger = OpportunityLedger()
    ledger.offer(workload_id="seismic", hazard=HazardKind.EARTHQUAKE,
                 scheduled_release_at=datetime.now(timezone.utc), captured_at=None,
                 correlation_id=uuid4())
    key = Ed25519PrivateKey.generate()
    signed = ledger.sign_schedule(key)
    assert OpportunityLedger.verify_signed_schedule(signed, key.public_key())["valid"] is True
    signed["schedule"][0]["workload_id"] = "tampered"
    assert OpportunityLedger.verify_signed_schedule(signed, key.public_key())["valid"] is False
