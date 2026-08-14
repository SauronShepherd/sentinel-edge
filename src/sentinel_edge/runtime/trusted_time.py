from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sentinel_edge.domain.models import (
    TimeOrigin,
    TimeSourceObservation,
    TimeTrustSnapshot,
    TimeTrustState,
)


@dataclass(frozen=True)
class TimeTrustPolicy:
    max_trusted_uncertainty_ms: float = 250.0
    max_display_uncertainty_ms: float = 10_000.0
    max_source_age_ms: float = 60_000.0
    disagreement_threshold_ms: float = 1_000.0
    authenticated_origins: frozenset[TimeOrigin] = frozenset({TimeOrigin.NTS})
    locally_trusted_origins: frozenset[TimeOrigin] = frozenset({TimeOrigin.FIXTURE})


class TrustedTimeManager:
    """Separates wall-clock origin/authentication from monotonic deadlines."""

    def __init__(self, policy: TimeTrustPolicy | None = None) -> None:
        self.policy = policy or TimeTrustPolicy()
        self._sources: dict[str, TimeSourceObservation] = {}
        self._clock_epoch = 0
        self._last_selected: TimeSourceObservation | None = None
        self._last_snapshot = TimeTrustSnapshot(
            state=TimeTrustState.UNUSABLE,
            selected_source_id=None,
            selected_origin=None,
            authenticated=False,
            uncertainty_ms=None,
            clock_epoch=0,
            display_time_allowed=False,
            security_validity_allowed=False,
            remote_freshness_allowed=False,
            peer_correlation_allowed=False,
            reason_codes=("no_time_source",),
            sources=(),
        )

    @staticmethod
    def _utc_ms(value: datetime) -> float:
        if value.tzinfo is None:
            raise ValueError("time source must carry timezone")
        return value.astimezone(timezone.utc).timestamp() * 1000.0

    def update(self, observation: TimeSourceObservation) -> TimeTrustSnapshot:
        previous = self._sources.get(observation.source_id)
        discontinuity_reasons: list[str] = []
        if previous is not None:
            if observation.clock_epoch < previous.clock_epoch:
                raise ValueError("time source clock epoch rollback")
            if observation.continuity_id == previous.continuity_id:
                expected_delta_ms = (observation.observed_monotonic_ns - previous.observed_monotonic_ns) / 1_000_000
                observed_delta_ms = self._utc_ms(observation.observed_utc) - self._utc_ms(previous.observed_utc)
                if observation.observed_monotonic_ns < previous.observed_monotonic_ns:
                    raise ValueError("time source monotonic rollback")
                if observed_delta_ms < -self.policy.disagreement_threshold_ms:
                    discontinuity_reasons.append("utc_rollback_detected")
                elif abs(observed_delta_ms - expected_delta_ms) > self.policy.disagreement_threshold_ms:
                    discontinuity_reasons.append("utc_step_detected")
            else:
                discontinuity_reasons.append("time_source_continuity_changed")
            if observation.authenticated != previous.authenticated:
                discontinuity_reasons.append("time_authentication_changed")
        self._sources[observation.source_id] = observation
        snapshot = self.evaluate(extra_reasons=tuple(discontinuity_reasons))
        self._last_snapshot = snapshot
        return snapshot

    def evaluate(self, *, extra_reasons: tuple[str, ...] = ()) -> TimeTrustSnapshot:
        reasons = list(extra_reasons)
        sources = tuple(sorted(self._sources.values(), key=lambda item: item.source_id))
        candidates = [item for item in sources if item.age_ms <= self.policy.max_source_age_ms]
        if not candidates:
            if sources:
                reasons.append("all_time_sources_stale")
            else:
                reasons.append("no_time_source")
            return TimeTrustSnapshot(
                state=TimeTrustState.UNUSABLE,
                selected_source_id=None,
                selected_origin=None,
                authenticated=False,
                uncertainty_ms=None,
                clock_epoch=self._clock_epoch,
                display_time_allowed=False,
                security_validity_allowed=False,
                remote_freshness_allowed=False,
                peer_correlation_allowed=False,
                reason_codes=tuple(sorted(set(reasons))),
                sources=sources,
            )

        trusted_candidates = [
            item for item in candidates
            if (
                (item.origin in self.policy.authenticated_origins and item.authenticated)
                or item.origin in self.policy.locally_trusted_origins
            )
            and item.uncertainty_ms <= self.policy.max_trusted_uncertainty_ms
        ]
        display_candidates = [item for item in candidates if item.uncertainty_ms <= self.policy.max_display_uncertainty_ms]
        selected_pool = trusted_candidates or display_candidates or candidates
        selected = min(selected_pool, key=lambda item: (item.uncertainty_ms, item.age_ms, item.source_id))

        if len(trusted_candidates) > 1:
            times = [self._utc_ms(item.observed_utc) for item in trusted_candidates]
            if max(times) - min(times) > self.policy.disagreement_threshold_ms:
                reasons.append("trusted_sources_disagree")

        if self._last_selected is not None:
            if selected.source_id != self._last_selected.source_id:
                reasons.append("selected_time_source_changed")
            if selected.authenticated != self._last_selected.authenticated:
                reasons.append("selected_time_authentication_changed")
            if selected.continuity_id != self._last_selected.continuity_id:
                reasons.append("selected_time_continuity_changed")
        if any(code in reasons for code in (
            "trusted_sources_disagree",
            "utc_rollback_detected",
            "utc_step_detected",
            "selected_time_authentication_changed",
            "selected_time_continuity_changed",
            "time_authentication_changed",
            "time_source_continuity_changed",
        )):
            self._clock_epoch += 1

        trusted = selected in trusted_candidates and "trusted_sources_disagree" not in reasons
        if trusted:
            state = TimeTrustState.TRUSTED
            security_allowed = True
            remote_freshness = True
            peer_correlation = True
            reasons.append("trusted_time_selected")
        elif selected in display_candidates:
            state = TimeTrustState.DISPLAY_ONLY
            security_allowed = False
            remote_freshness = False
            peer_correlation = False
            reasons.append("unauthenticated_or_uncertain_time_display_only")
        else:
            state = TimeTrustState.DEGRADED
            security_allowed = False
            remote_freshness = False
            peer_correlation = False
            reasons.append("time_uncertainty_exceeds_display_policy")

        if selected.origin is TimeOrigin.NTP and not selected.authenticated:
            reasons.append("unauthenticated_ntp_cannot_strengthen_security")
            security_allowed = remote_freshness = peer_correlation = False
            if state is TimeTrustState.TRUSTED:
                state = TimeTrustState.DISPLAY_ONLY
        if selected.certificate_bootstrap_valid is False:
            reasons.append("certificate_bootstrap_invalid")
            security_allowed = remote_freshness = peer_correlation = False
            state = TimeTrustState.DEGRADED

        self._last_selected = selected
        return TimeTrustSnapshot(
            state=state,
            selected_source_id=selected.source_id,
            selected_origin=selected.origin,
            authenticated=selected.authenticated,
            uncertainty_ms=selected.uncertainty_ms,
            clock_epoch=self._clock_epoch,
            display_time_allowed=state is not TimeTrustState.UNUSABLE,
            security_validity_allowed=security_allowed,
            remote_freshness_allowed=remote_freshness,
            peer_correlation_allowed=peer_correlation,
            reason_codes=tuple(sorted(set(reasons))),
            sources=sources,
        )

    @property
    def snapshot(self) -> TimeTrustSnapshot:
        return self._last_snapshot

    def register_fixture(self, *, now: datetime, monotonic_ns: int = 0, source_id: str = "scenario-fixture-clock") -> TimeTrustSnapshot:
        return self.update(TimeSourceObservation(
            source_id=source_id,
            origin=TimeOrigin.FIXTURE,
            authenticated=False,
            observed_utc=now,
            observed_monotonic_ns=monotonic_ns,
            uncertainty_ms=0.0,
            age_ms=0.0,
            stratum=None,
            reference_id="signed-scenario-manifest",
            continuity_id="fixture-continuity-v1",
            clock_epoch=0,
            certificate_bootstrap_valid=True,
        ))
