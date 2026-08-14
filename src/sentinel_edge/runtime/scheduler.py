from __future__ import annotations

import heapq
import math
from datetime import datetime, timedelta
from itertools import count
from uuid import UUID, uuid4

from sentinel_edge.domain.models import (
    CriticalityTier,
    JobRequest,
    JobStatus,
    OpportunityDisposition,
    ResourceSnapshot,
    RuntimeMode,
    SchedulerSnapshot,
    WorkloadSpec,
)
from sentinel_edge.runtime.clock import Clock, SystemClock
from sentinel_edge.runtime.opportunities import OpportunityLedger


class AdmissionError(RuntimeError):
    pass


class WorkloadScheduler:
    """Component 3 scheduler: fixed criticality, EDF within tier, monotonic deadlines, and bounded admission."""

    component_id = "component-3-runtime"

    def __init__(
        self,
        queue_limit: int = 256,
        tier_a_reserve_memory_mb: int = 64,
        *,
        clock: Clock | None = None,
        mode: RuntimeMode = RuntimeMode.DEVELOPMENT,
        approved_profile_ids: set[str] | None = None,
        opportunity_ledger: OpportunityLedger | None = None,
        known_safe_interference_pairs: set[tuple[str, str]] | None = None,
    ) -> None:
        self.queue_limit = queue_limit
        self.tier_a_reserve_memory_mb = tier_a_reserve_memory_mb
        self.clock = clock or SystemClock()
        self.mode = mode
        self._approved_profiles = approved_profile_ids
        self._registry: dict[str, WorkloadSpec] = {}
        self._queue: list[tuple[int, int, int, JobRequest]] = []
        self._counter = count()
        self._active: dict[UUID, JobRequest] = {}
        self._deferred_ids: set[UUID] = set()
        self.degradation_level = 0
        self.overloaded = False
        self.reason_codes: list[str] = []
        self.opportunities = opportunity_ledger or OpportunityLedger()
        self._known_safe_interference_pairs = {
            tuple(sorted(pair)) for pair in (known_safe_interference_pairs or set())
        }
        self._frozen = False

    def register(self, spec: WorkloadSpec) -> None:
        if self._frozen:
            raise ValueError("workload registry is frozen")
        if self._approved_profiles is not None and spec.profile_id not in self._approved_profiles:
            raise ValueError(f"profile is not approved: {spec.profile_id}")
        if spec.workload_id in self._registry and self._registry[spec.workload_id] != spec:
            raise ValueError("workload registration is immutable")
        self._registry[spec.workload_id] = spec

    def freeze(self) -> None:
        self._frozen = True

    def reallocate_cadence(self, workload_id: str, *, multiplier: float, reason_code: str) -> WorkloadSpec:
        """Apply a bounded cadence change from fresh evidence/context.

        The registry remains immutable in benchmark/judge mode; development
        orchestration may adjust only future opportunities and records why.
        """
        if self._frozen:
            raise ValueError("workload registry is frozen")
        if workload_id not in self._registry:
            raise KeyError(workload_id)
        if not math.isfinite(multiplier) or multiplier <= 0:
            raise ValueError("cadence multiplier must be finite and positive")
        if not reason_code.strip():
            raise ValueError("cadence reallocation requires a reason code")
        current = self._registry[workload_id]
        updated = current.model_copy(update={"period_ms": max(1, math.ceil(current.period_ms / multiplier))})
        self._registry[workload_id] = updated
        self._declare_overload(f"cadence_reallocated:{reason_code.strip()}")
        return updated

    def submit(
        self,
        workload_id: str,
        payload: dict,
        released_at: datetime | None = None,
        *,
        scheduled_release_at: datetime | None = None,
        captured_at: datetime | None = None,
        correlation_id: UUID | None = None,
    ) -> JobRequest:
        if workload_id not in self._registry:
            raise KeyError(workload_id)
        if len(self._queue) >= self.queue_limit:
            raise AdmissionError("bounded queue is full")
        if self.mode in {RuntimeMode.BENCHMARK, RuntimeMode.JUDGE}:
            self.freeze()
        released_at = released_at or self.clock.now_utc()
        scheduled_release_at = scheduled_release_at or released_at
        correlation_id = correlation_id or uuid4()
        spec = self._registry[workload_id]
        release_ns = self.clock.monotonic_ns()
        deadline_ns = release_ns + spec.deadline_ms * 1_000_000
        opportunity = self.opportunities.offer(
            workload_id=spec.workload_id,
            hazard=spec.hazard,
            scheduled_release_at=scheduled_release_at,
            captured_at=captured_at,
            correlation_id=correlation_id,
        )
        job = JobRequest(
            opportunity_id=opportunity.opportunity_id,
            correlation_id=correlation_id,
            workload=spec,
            released_at=released_at,
            absolute_deadline=released_at + timedelta(milliseconds=spec.deadline_ms),
            released_monotonic_ns=release_ns,
            deadline_monotonic_ns=deadline_ns,
            payload=payload,
        )
        self.opportunities.mark_queued(job.opportunity_id, released_at, release_ns, deadline_ns)
        heapq.heappush(self._queue, (int(spec.tier), deadline_ns, next(self._counter), job))
        return job

    def dispatch(self, resources: ResourceSnapshot, now: datetime | None = None) -> JobRequest | None:
        del now  # wall time must not affect local deadline ordering
        if not self._queue:
            return None
        now_ns = self.clock.monotonic_ns()
        held: list[tuple[int, int, int, JobRequest]] = []
        selected: JobRequest | None = None
        while self._queue:
            item = heapq.heappop(self._queue)
            job = item[3]
            admissible, terminal_reason = self._admissible(job, resources, now_ns)
            if terminal_reason:
                job.status = JobStatus.REJECTED
                if terminal_reason not in job.reason_codes:
                    job.reason_codes.append(terminal_reason)
                self.opportunities.mark_terminal(
                    job.opportunity_id,
                    OpportunityDisposition.SKIPPED,
                    now_ns,
                    terminal_reason,
                )
                continue
            if admissible:
                selected = job
                break
            job.deferral_count += 1
            job.status = JobStatus.DEFERRED
            reason = "resource_admission_deferred"
            if reason not in job.reason_codes:
                job.reason_codes.append(reason)
            self._deferred_ids.add(job.job_id)
            self.opportunities.mark_deferred(job.opportunity_id, reason)
            held.append(item)
        for item in held:
            heapq.heappush(self._queue, item)
        if selected:
            selected.status = JobStatus.RUNNING
            selected.service_started_monotonic_ns = now_ns
            self._deferred_ids.discard(selected.job_id)
            self._active[selected.job_id] = selected
            self.opportunities.mark_started(selected.opportunity_id, now_ns)
        return selected

    def _admissible(self, job: JobRequest, resources: ResourceSnapshot, now_ns: int) -> tuple[bool, str | None]:
        spec = job.workload
        # Tier-A interference is unsafe to assume away.  If a pair has no
        # measured/declared safe profile, serialize it behind the active job.
        # This is deliberately conservative and deterministic: unknown pairs
        # never co-run merely because resources look available.
        for active in self._active.values():
            pair = tuple(sorted((active.workload.workload_id, spec.workload_id)))
            if (active.workload.tier == CriticalityTier.A_IMMEDIATE or spec.tier == CriticalityTier.A_IMMEDIATE) and pair not in self._known_safe_interference_pairs:
                if "unknown_tier_a_interference_serialized" not in job.reason_codes:
                    job.reason_codes.append("unknown_tier_a_interference_serialized")
                return False, None
        elapsed_ms = (now_ns - job.released_monotonic_ns) / 1_000_000
        deferral_expired = elapsed_ms >= spec.max_deferral_ms
        deadline_missed = now_ns > job.deadline_monotonic_ns

        if resources.available_memory_mb < spec.memory_mb:
            self._declare_overload("insufficient_memory")
            if deferral_expired:
                return False, "max_deferral_exceeded_insufficient_memory"
            return False, None

        # A configured forced scan is an opportunity guarantee, not merely
        # metadata. Once its cadence expires, admit the workload ahead of
        # lower-tier reserve/overload deferral when the job's own memory can
        # still be satisfied. This preserves bounded service without claiming
        # hard preemption of an already-running job.
        forced_scan_due = bool(spec.forced_scan_ms and elapsed_ms >= spec.forced_scan_ms)
        if forced_scan_due:
            self._declare_overload("forced_scan_due")
            return True, None

        if spec.tier == CriticalityTier.A_IMMEDIATE:
            if deadline_missed:
                self._declare_overload("tier_a_deadline_miss")
            return True, None

        reserve = self.tier_a_reserve_memory_mb
        if resources.available_memory_mb - spec.memory_mb < reserve:
            if deferral_expired:
                self._declare_overload("tier_a_reserve_conflict")
                if spec.tier <= CriticalityTier.C_TIMELY:
                    return True, None
                return False, "max_deferral_exceeded_reserve"
            return False, None

        if resources.overloaded:
            self.degradation_level = max(self.degradation_level, 1)
            self._declare_overload("node_overload")
            if spec.tier <= CriticalityTier.B_URGENT:
                return True, None
            if deferral_expired and spec.tier <= CriticalityTier.C_TIMELY:
                return True, None
            if deferral_expired:
                return False, "max_deferral_exceeded_overload"
            return False, None

        if deadline_missed:
            self._declare_overload("deadline_miss")
            return True, None
        return True, None

    def _declare_overload(self, reason: str) -> None:
        self.overloaded = True
        self.degradation_level = max(self.degradation_level, 1)
        if reason not in self.reason_codes:
            self.reason_codes.append(reason)

    def complete(self, job: JobRequest) -> None:
        if job.status is not JobStatus.RUNNING:
            raise ValueError("only running jobs can complete")
        now_ns = self.clock.monotonic_ns()
        job.status = JobStatus.COMPLETED
        job.completed_monotonic_ns = now_ns
        self._active.pop(job.job_id, None)
        self.opportunities.mark_terminal(job.opportunity_id, OpportunityDisposition.PROCESSED, now_ns)

    def fallback_schedule(self) -> tuple[str, ...]:
        if "static_fallback_active" not in self.reason_codes:
            self.reason_codes.append("static_fallback_active")
        return tuple(spec.workload_id for spec in sorted(self._registry.values(), key=lambda s: (int(s.tier), s.workload_id)))

    def snapshot(self) -> SchedulerSnapshot:
        queued_jobs = [item[3] for item in self._queue]
        queued = tuple(sorted(job.workload.workload_id for job in queued_jobs if job.job_id not in self._deferred_ids))
        deferred = tuple(sorted(job.workload.workload_id for job in queued_jobs if job.job_id in self._deferred_ids))
        active = tuple(sorted(job.workload.workload_id for job in self._active.values()))
        present = set(active) | set(queued) | set(deferred)
        sleeping = tuple(sorted(set(self._registry) - present))
        return SchedulerSnapshot(
            active=active,
            queued=queued,
            deferred=deferred,
            sleeping=sleeping,
            overloaded=self.overloaded,
            degradation_level=self.degradation_level,
            reason_codes=tuple(sorted(set(self.reason_codes))),
        )

    @property
    def queued(self) -> int:
        return len(self._queue)

    @property
    def registry(self) -> tuple[WorkloadSpec, ...]:
        return tuple(sorted(self._registry.values(), key=lambda spec: spec.workload_id))
